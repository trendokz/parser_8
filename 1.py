# способ как находить по части слова, все слова имеющие эту часть!!!

import re

text = 'product-detail-aside__badge-price product-card__badge-price--red dfghgdfghgdfhfgjh' \
       'dfghg product-detail-aside__badge-price product-card__badge-price--violet'

text_copy = 'product-detail-aside__badge-price product-card__badge-price--\w+'


words = re.findall(text_copy, text)

print(words)


