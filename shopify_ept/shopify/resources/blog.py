from ..base import ShopifyResource
from ...shopify import mixins
from ... import shopify


class Blog(ShopifyResource, mixins.Metafields, mixins.Events):

    def articles(self):
        return shopify.Article.find(blog_id=self.id)
