import subprocess
import shutil
import logging
import os
import signal
import sys
import threading
from pathlib import Path
from fastapi import HTTPException, status

logger = logging.getLogger("ffmpeg_runner")

# Thread-safe registry to track active FFmpeg subprocesses for automated killer
_active_processes_lock = threading.Lock()
_active_processes: set[subprocess.Popen] = set()

def get_ffmpeg_binary() -> str:
    """Find system ffmpeg or fallback to imageio-ffmpeg bundled binary."""
    ffmpeg_sys = shutil.which("ffmpeg")
    if ffmpeg_sys:
        return ffmpeg_sys
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def get_ffprobe_binary() -> str:
    ffprobe_sys = shutil.which("ffprobe")
    if ffprobe_sys:
        return ffprobe_sys
    return "ffprobe"

def kill_process_tree(proc: subprocess.Popen):
    """Safely and aggressively terminate a process and all its child threads."""
    if proc.poll() is not None:
        return  # Process already finished
    
    try:
        if sys.platform == "win32":
            proc.kill()
        else:
            # On Linux / VPS, kill entire process group
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                proc.kill()
    except Exception as e:
        logger.warning(f"Error killing ffmpeg process {proc.pid}: {e}")

def run_ffmpeg(args: list[str], timeout_seconds: int = 45) -> subprocess.CompletedProcess:
    """
    Safely execute ffmpeg with CPU & RAM throttling for 2C2G servers (max 2 threads)
    and aggressive auto-killer to eliminate orphan / hanging processes.
    """
    ffmpeg_bin = get_ffmpeg_binary()
    
    # Strictly limit CPU threads to 2 so 2C2G server never spikes to 100%
    command = [ffmpeg_bin, "-y", "-threads", "2"] + args
    
    logger.info(f"Running safe throttled FFmpeg: {' '.join(command[:6])} ...")
    
    # Process group configuration for clean termination
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
    }
    
    if sys.platform != "win32":
        kwargs["preexec_fn"] = os.setsid
    else:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP") else 0

    proc = subprocess.Popen(command, **kwargs)
    
    with _active_processes_lock:
        _active_processes.add(proc)
        
    try:
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
        
        if proc.returncode != 0:
            logger.error(f"FFmpeg failed with code {proc.returncode}: {stderr[:300]}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "VIDEO_PROCESSING_FAILED", "message": "Video processing failed. Please verify media format."}
            )
            
        return subprocess.CompletedProcess(command, proc.returncode, stdout, stderr)
        
    except subprocess.TimeoutExpired:
        logger.warning(f"FFmpeg process {proc.pid} exceeded timeout ({timeout_seconds}s). Auto-killing process...")
        kill_process_tree(proc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"code": "TIMEOUT", "message": "Video processing timed out. Uploaded video exceeds processing limit."}
        )
    except Exception as e:
        kill_process_tree(proc)
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"FFmpeg execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "PROCESSING_ERROR", "message": f"Media processing error: {str(e)}"}
        )
    finally:
        # Guarantee process is dead and removed from active set
        kill_process_tree(proc)
        with _active_processes_lock:
            _active_processes.discard(proc)
