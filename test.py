
from urllib.parse import quote

numbers = "1,2,3"
encoded_numbers = quote(numbers)
print(encoded_numbers)
