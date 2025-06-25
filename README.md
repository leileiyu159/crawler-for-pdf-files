# crawler-for-pdf-files
Automatically batch crawl pdf files from websites, such as guides and academic papers, to facilitate academic research
Note：
1：If you use a vpn to access the website，Remember to configure your proxies in proxies.（Prevent SSL/TLS handshake failure during the proxy connection process）

2：This code crawled the lung cancer guidance from the NICE website as an example.If the website you want to crawl has an anti-crawling mechanism, remember to add the anti-crawling code by yourself.

3：This code traverses the detail pages of each guide and looks for the PDF download link on each detail page.
（If the website you visit can directly download the pdf without the need to visit the detail page, delete the logic corresponding to accessing the detail page in the code.）

4：If you want to name the file yourself, please modify the corresponding naming logic.



      

