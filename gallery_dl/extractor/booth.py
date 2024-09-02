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
    SHOP_PATTERN = r"(?:https?://)?(?:(?!www\.)([\w-]+))\.booth\.pm"

    category = "booth"
    root = "https://www.booth.pm"
    directory_fmt = ("{category}", "{shopName}")
    filename_fmt = "{id}_{num}.{extension}"
    archive_fmt = "{id}_{num}"
    # _warning = True

    def _init(self):
        self.config("")
        pass

    def _get_product_data(self, shop_id, product_id):
        url = f"https://booth.pm/en/items/{product_id}"
        metadata: Dict = self.request(url, headers={"Accept": "application/json"}).json()
        metadata.pop("tag_banners")
        metadata["tags"] = [x["name"] for x in metadata["tags"]]  # discard the tag url
        html = self.request(url).text
        images_mata = metadata.pop("images")
        metadata["images"] = zip(
            (x["caption"] for x in images_mata),
            text.extract_iter(html, begin='data-origin="', end='"'),
        )
        return metadata

    def _get_image_url_from_metadata(self, metadata: Dict):
        metadata = metadata.copy()
        images = metadata.pop("images")
        for i, (caption, url) in enumerate(images):
            metadata["num"] = i + 1
            metadata["image_url"] = url
            metadata["extension"] = url.split(".")[-1]
            metadata["image_caption"] = caption
            yield Message.Url, url, metadata

    def items(self):
        raise NotImplementedError


class BoothProductExtractor(BoothExtractor):
    """Extractor for preview pictures from a single BOOTH product"""

    subcategory = "product"
    __pattern0 = BoothExtractor.SHOP_PATTERN + r"/items/(\d+)"
    __pattern1 = BoothExtractor.BASE_PATTERN + r"/(?:w+/)?items/(\d+)"
    pattern = __pattern0 + r"|" + __pattern1
    example = "https://SHOP.booth.pm/items/12345 or https://booth.pm/en/items/12345"

    def __init__(self, match):
        super().__init__(match)
        self.shop_id = match.group(1)
        self.product_id = match.group(2)

    def _get_product_data(self):
        return super()._get_product_data(self.shop_id, self.product_id)

    def items(self):
        metadata = self._get_product_data()
        yield Message.Directory, metadata
        yield from self._get_image_url_from_metadata(metadata)
