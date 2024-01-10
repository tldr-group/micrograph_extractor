def detect_composite_image_from_caption(caption: str) -> bool:
    if "(a)" in caption.lower() or " a. " in caption.lower():
        return True
    else:
        return False


# TODO: add check micrograph code based on caption
# TODO: add check instrument code based on caption
