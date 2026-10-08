import pymupdf
from PIL import Image
from pathlib import Path
from pdf2docx import Converter
from fastapi import HTTPException, status
from app.utils.files import get_unique_filename, get_result_filepath

class PdfService:
    @staticmethod
    def images_to_pdf(image_paths: list[Path]) -> Path:
        out_filename = get_unique_filename("document.pdf", prefix="img2pdf")
        out_path = get_result_filepath(out_filename)
        
        try:
            images = []
            for path in image_paths:
                img = Image.open(path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                images.append(img)
                
            if not images:
                raise ValueError("No valid images provided.")
                
            first_img = images[0]
            rest_imgs = images[1:] if len(images) > 1 else []
            first_img.save(out_path, save_all=True, append_images=rest_imgs)
            return out_path
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "PDF_CREATION_FAILED", "message": f"Failed to create PDF from images: {str(e)}"}
            )

    @staticmethod
    def pdf_to_images(pdf_path: Path, format_type: str = 'jpg', dpi: int = 150) -> list[Path]:
        try:
            doc = pymupdf.open(pdf_path)
            result_paths = []
            ext = format_type.lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                ext = 'jpg'
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(dpi=dpi)
                page_filename = f"{pdf_path.stem}_page_{page_num + 1}.{ext}"
                out_path = get_result_filepath(page_filename)
                
                if ext in ['png', 'jpg', 'jpeg']:
                    pix.save(str(out_path))
                elif ext == 'webp':
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img.save(str(out_path), "WEBP", quality=90)
                    
                result_paths.append(out_path)
                
            doc.close()
            return result_paths
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "PDF_EXTRACTION_FAILED", "message": f"Failed to convert PDF pages: {str(e)}"}
            )

    @staticmethod
    def pdf_to_docx(pdf_path: Path) -> Path:
        """
        Converts PDF into editable Word (.docx) document with full Khmer Unicode (ភាសាខ្មែរ)
        and multi-lingual complex script font mapping.
        """
        out_filename = get_unique_filename(pdf_path.name, prefix="converted_doc")
        out_filename = str(Path(out_filename).stem) + ".docx"
        out_path = get_result_filepath(out_filename)

        import re
        from docx import Document
        from docx.shared import Inches, Pt
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        import io

        def apply_unicode_font(run, font_name="Khmer OS Content", size_pt=11):
            run.font.name = font_name
            run.font.size = Pt(size_pt)
            try:
                rPr = run._r.get_or_add_rPr()
                rFonts = OxmlElement('w:rFonts')
                rFonts.set(qn('w:ascii'), 'Calibri')
                rFonts.set(qn('w:hAnsi'), 'Calibri')
                rFonts.set(qn('w:cs'), font_name)
                rFonts.set(qn('w:eastAsia'), font_name)
                rPr.append(rFonts)
            except Exception:
                pass

        # Engine 1: High-fidelity pdf2docx
        try:
            cv = Converter(str(pdf_path))
            cv.convert(str(out_path), start=0, end=None)
            cv.close()
            if out_path.exists() and out_path.stat().st_size > 100:
                doc_check = Document(str(out_path))
                doc_text = " ".join([p.text for p in doc_check.paragraphs])
                if len(doc_text.strip()) > 10:
                    return out_path
        except Exception as e:
            print(f"pdf2docx primary engine note: {e}, running resilient PyMuPDF+Khmer Unicode builder...")

        # Engine 2: Resilient PyMuPDF + Khmer Unicode Word Builder
        try:
            doc_pdf = pymupdf.open(pdf_path)
            doc_word = Document()

            for page_num in range(len(doc_pdf)):
                page = doc_pdf[page_num]
                
                # Extract text blocks
                text = page.get_text("text").strip()
                has_khmer = bool(re.search(r'[\u1780-\u17FF]', text))
                font_name = "Khmer OS Content" if has_khmer else "Calibri"

                if text:
                    for paragraph in text.split('\n\n'):
                        p_clean = paragraph.strip()
                        if p_clean:
                            p = doc_word.add_paragraph()
                            run = p.add_run(p_clean)
                            apply_unicode_font(run, font_name=font_name, size_pt=11)
                
                # Extract images
                image_list = page.get_images(full=True)
                for img_info in image_list[:4]:
                    try:
                        xref = img_info[0]
                        base_img = doc_pdf.extract_image(xref)
                        img_bytes = base_img["image"]
                        img_stream = io.BytesIO(img_bytes)
                        doc_word.add_picture(img_stream, width=Inches(5.5))
                    except Exception:
                        pass
                
                # If page is a complex Khmer layout or scanned document without extractable text, render visual page
                if (not text or len(text) < 5) and not image_list:
                    pix = page.get_pixmap(dpi=200)
                    img_stream = io.BytesIO(pix.tobytes("png"))
                    doc_word.add_picture(img_stream, width=Inches(6.0))

                if page_num < len(doc_pdf) - 1:
                    doc_word.add_page_break()

            doc_pdf.close()
            doc_word.save(str(out_path))
            return out_path
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "PDF_TO_WORD_FAILED", "message": f"Failed to convert PDF to Word: {str(e)}"}
            )

    @staticmethod
    def pdf_to_text(pdf_path: Path) -> str:
        try:
            doc = pymupdf.open(pdf_path)
            text_pages = []
            for page_num, page in enumerate(doc):
                text = page.get_text()
                text_pages.append(f"--- Page {page_num + 1} ---\n{text}")
            doc.close()
            return "\n\n".join(text_pages)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "PDF_TEXT_EXTRACTION_FAILED", "message": f"Failed to extract text from PDF: {str(e)}"}
            )

    @staticmethod
    def merge_pdfs(pdf_paths: list[Path]) -> Path:
        out_filename = get_unique_filename("merged_doc.pdf", prefix="merged")
        out_path = get_result_filepath(out_filename)
        
        try:
            merged_doc = pymupdf.open()
            for p in pdf_paths:
                doc = pymupdf.open(p)
                merged_doc.insert_pdf(doc)
                doc.close()
                
            merged_doc.save(out_path)
            merged_doc.close()
            return out_path
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "PDF_MERGE_FAILED", "message": f"Failed to merge PDF files: {str(e)}"}
            )

    @staticmethod
    def split_pdf(pdf_path: Path, page_ranges: str) -> Path:
        out_filename = get_unique_filename(pdf_path.name, prefix="split")
        out_path = get_result_filepath(out_filename)
        
        try:
            doc = pymupdf.open(pdf_path)
            split_doc = pymupdf.open()
            
            # Parse page ranges like "1-3, 5, 7-9"
            total_pages = len(doc)
            selected_pages = set()
            
            for part in page_ranges.split(','):
                part = part.strip()
                if '-' in part:
                    start_str, end_str = part.split('-')
                    start = max(1, int(start_str.strip()))
                    end = min(total_pages, int(end_str.strip()))
                    for p in range(start, end + 1):
                        selected_pages.add(p - 1)
                elif part.isdigit():
                    p = int(part)
                    if 1 <= p <= total_pages:
                        selected_pages.add(p - 1)
                        
            for page_idx in sorted(selected_pages):
                split_doc.insert_pdf(doc, from_page=page_idx, to_page=page_idx)
                
            split_doc.save(out_path)
            doc.close()
            split_doc.close()
            return out_path
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "PDF_SPLIT_FAILED", "message": f"Failed to split PDF: {str(e)}"}
            )

    @staticmethod
    def compress_pdf(pdf_path: Path) -> dict:
        out_filename = get_unique_filename(pdf_path.name, prefix="compressed")
        out_path = get_result_filepath(out_filename)
        orig_size = pdf_path.stat().st_size
        
        try:
            doc = pymupdf.open(pdf_path)
            doc.save(out_path, garbage=4, deflate=True, clean=True)
            doc.close()
            
            comp_size = out_path.stat().st_size
            saved_percent = round(((orig_size - comp_size) / orig_size) * 100, 1) if orig_size > 0 else 0
            
            return {
                "file_path": out_path,
                "original_size": orig_size,
                "compressed_size": comp_size,
                "saved_percent": max(0, saved_percent)
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "PDF_COMPRESS_FAILED", "message": f"Failed to compress PDF: {str(e)}"}
            )
