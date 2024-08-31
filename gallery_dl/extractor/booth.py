# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://booth.pm/"""

from typing import Dict
from .common import Extractor, Message
from .. import text
from ..cache import memcache


class BoothExtractor(Extractor):
    """Base class for BOOTH extractors"""

    BASE_PATTERN = r"(?:https?://)?(?:www\.)?booth\.pm"
    SELLER_PATTERN = r"(?:https?://)?(?:(?!www\.)([\w-]+))\.booth\.pm"

    category = "booth"
    root = "https://www.booth.pm"
    directory_fmt = ("{category}", "{sellerName}")
    filename_fmt = "{id}_{num}.{extension}"
    archive_fmt = "{id}_{num}"
    # _warning = True

    def _init(self):
        pass

    def _get_product_data(self, seller_id, product_id):
        url = f"https://{seller_id}.booth.pm/items/{product_id}"
        # url = f"https://booth.pm/items/{product_id}"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        response = self.request(url, headers=headers)
        metadata: Dict = response.json()
        metadata.pop("tag_banners")
        metadata["tags"] = [x["name"] for x in metadata["tags"]]  # discard the tag url
        return metadata

    def _get_image_url_from_metadata(self, metadata: Dict):
        metadata = metadata.copy()
        images = metadata.pop("images")
        for i, image_meta in enumerate(images):
            # image_meta: {"caption": ..., "original": ..., "resized": ...}
            original: str = image_meta["original"].replace("_base_resized", "")
            fallback = (
                image_meta["original"].replace("_base_resized.jpg", ".PNG"),
                image_meta["original"],
            )
            metadata["num"] = i + 1
            metadata["image_url"] = original
            metadata["extension"] = original.split(".")[-1]
            metadata["_fallback"] = fallback
            metadata["image_meta"] = image_meta
            yield Message.Url, original, metadata

    def items(self):
        raise NotImplementedError


class BoothProductExtractor(BoothExtractor):
    """Extractor for preview pictures from a single BOOTH product"""

    subcategory = "product"
    pattern = BoothExtractor.SELLER_PATTERN + r"/items/(\d+)"
    example = "https://SELLER.booth.pm/items/12345"

    def __init__(self, match):
        BoothExtractor.__init__(self, match)
        self.seller_id = match.group(1)
        self.product_id = match.group(2)

    def _get_product_data(self):
        return super()._get_product_data(self.seller_id, self.product_id)

    def items(self):
        metadata = self._get_product_data()
        yield Message.Directory, metadata
        yield from self._get_image_url_from_metadata(metadata)
