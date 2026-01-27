# import pandas as pd


# file_path = r'C:\Users\ankun\NewdjangoEnv\Product_scraping\backend\data\cleaned_products.json'
# def export_to_csv(data: list[dict], file_path: str) -> None:
#     df = pd.DataFrame(data)
#     df.to_csv(file_path, index=False)
#     return df

# if __name__ == "__main__":
#     data = pd.read_json(file_path)
#     print(f"Data loaded from {file_path}, total records: {len(data)}")
#     csv_path = file_path.replace('.json', '.csv')
#     data.to_csv(csv_path, index=False)
#     print(f"Data exported to {csv_path}")
    
from DrissionPage import ChromiumPage
import json, re

product_url = "https://www.wegetanystock.com/grocery"
page = ChromiumPage()
page.get(product_url)

html = page.html
match = re.search(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    html,
    re.S
)

script = page.ele('#__NEXT_DATA__')
data = json.loads(script.text)


