from pathlib import Path
from fastapi import HTTPException, status
from app.utils.files import get_unique_filename, get_result_filepath
from app.utils.ffmpeg_runner import run_ffmpeg

class VideoService:
    @staticmethod
    def convert_video(input_path: Path, output_format: str) -> Path:
        out_format = output_format.lower().strip('.')
        out_filename = f"{input_path.stem}_converted.{out_format}"
        out_path = get_result_filepath(out_filename)
        
        args = [
            "-i", str(input_path),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "26",
            "-c:a", "aac",
            "-b:a", "128k",
            str(out_path)
        ]
        if out_format == "webm":
            args = [
                "-i", str(input_path),
                "-c:v", "libvpx-vp9",
                "-crf", "32",
                "-b:v", "0",
                "-c:a", "libopus",
                str(out_path)
            ]
            
        run_ffmpeg(args, timeout_seconds=45)
        return out_path

    @staticmethod
    def compress_video(input_path: Path, crf: int = 28) -> dict:
        orig_size = input_path.stat().st_size
        out_filename = f"compressed_{input_path.name}"
        out_path = get_result_filepath(out_filename)
        
        args = [
            "-i", str(input_path),
            "-vcodec", "libx264",
            "-crf", str(crf),
            "-preset", "veryfast",
            "-acodec", "aac",
            "-b:a", "96k",
            str(out_path)
        ]
        run_ffmpeg(args, timeout_seconds=45)
        
        new_size = out_path.stat().st_size
        saved_bytes = max(0, orig_size - new_size)
        saved_percent = round((saved_bytes / orig_size) * 100, 1) if orig_size > 0 else 0
        
        return {
            "file_path": out_path,
            "original_size": orig_size,
            "compressed_size": new_size,
            "saved_bytes": saved_bytes,
            "saved_percent": saved_percent
        }

    @staticmethod
    def video_to_mp3(input_path: Path, bitrate: str = "192k") -> Path:
        out_filename = f"{input_path.stem}_audio.mp3"
        out_path = get_result_filepath(out_filename)
        
        args = [
            "-i", str(input_path),
            "-vn",
            "-acodec", "libmp3lame",
            "-b:a", bitrate,
            str(out_path)
        ]
        run_ffmpeg(args, timeout_seconds=45)
        return out_path

    @staticmethod
    def video_to_gif(input_path: Path, fps: int = 12, width: int = 480) -> Path:
        out_filename = f"{input_path.stem}.gif"
        out_path = get_result_filepath(out_filename)
        
        # High quality 2-pass palette with max 10s duration to prevent memory overload
        vf = f"fps={fps},scale={width}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        args = [
            "-i", str(input_path),
            "-t", "10",
            "-vf", vf,
            str(out_path)
        ]
        run_ffmpeg(args, timeout_seconds=45)
        return out_path

    @staticmethod
    def resize_video(input_path: Path, width: int, height: int) -> Path:
        out_filename = f"resized_{input_path.name}"
        out_path = get_result_filepath(out_filename)
        
        vf = f"scale={width}:{height}"
        args = [
            "-i", str(input_path),
            "-vf", vf,
            "-preset", "ultrafast",
            "-c:a", "copy",
            str(out_path)
        ]
        run_ffmpeg(args, timeout_seconds=45)
        return out_path
