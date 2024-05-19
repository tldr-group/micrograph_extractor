from os import getcwd, makedirs
from os.path import join
from extract import extract_figures_captions, single_pdf_extract_process, CWD


def test_extraction():
    target_dir = join(CWD, "test_data/")
    target_pdf = join(target_dir, "tmp.pdf")

    out_img_dir = join(CWD, "test_data/out/imgs/")
    out_data_dir = join(CWD, "test_data/out/")

    processed_dir = join(CWD, "test_data/processed/")

    for new_dir in [target_dir, out_img_dir, processed_dir]:
        makedirs(new_dir, exist_ok=True)

    captions, paths = single_pdf_extract_process(
        target_pdf, out_img_dir, out_data_dir, processed_dir
    )
    print(captions)


if __name__ == "__main__":
    test_extraction()
