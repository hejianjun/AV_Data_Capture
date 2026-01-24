from lxml import etree

from mdc.scraping.airav import Airav


def test_airav_query_number_url_selects_exact_match(monkeypatch):
    html = """
    <html><body>
      <div class="row row-cols-2 row-cols-lg-4 g-2 mt-0">
          <div class="col oneVideo">
                        <div class="card h-100">
                            <div class="oneVideo-top">
                                <a href="/video?hid=132292">
                                    <img src="https://airav.io/storage/cover/big/132292.jpg?1769171547" class="card-img-top" alt="..." onerror="changeImageSrc(this)">
                                    
                                </a>
                            </div>
                            <div class="oneVideo-body">
                                <h5>CESD-854 喜歡腥臭肉棒與精液的淫語痴女・川上優的性愛</h5>
                                <div class="oneVideo-fotter">
                                    <p><i class="fa fa-eye"></i>22666</p>
                                    <p><i class="fa fa-heart"></i>22666</p>
                                </div>
                            </div>
                        </div>
                    </div>
                                    <div class="col oneVideo">
                        <div class="card h-100">
                            <div class="oneVideo-top">
                                <a href="/video?hid=99-21-21680">
                                    <img src="https://airav.io/storage/cover/big/99-21-21680.jpg?1769153616" class="card-img-top" alt="..." onerror="changeImageSrc(this)">
                                    
                                </a>
                            </div>
                            <div class="oneVideo-body">
                                <h5>CESD-854 喜歡腥臭肉棒與精液的淫語痴女・川上優的性愛</h5>
                                <div class="oneVideo-fotter">
                                    <p><i class="fa fa-eye"></i>8416</p>
                                    <p><i class="fa fa-heart"></i>8416</p>
                                </div>
                            </div>
                        </div>
                    </div>
                                    <div class="col oneVideo">
                        <div class="card h-100">
                            <div class="oneVideo-top">
                                <a href="/video?hid=110394">
                                    <img src="https://airav.io/storage/cover/big/110394.jpg?1769206915" class="card-img-top" alt="..." onerror="changeImageSrc(this)">
                                    
                                </a>
                            </div>
                            <div class="oneVideo-body">
                                <h5>DASD-854 使用催眠術無慈悲插入 陰沉委員長被惡劣教師無套抽插 朝比奈七瀨</h5>
                                <div class="oneVideo-fotter">
                                    <p><i class="fa fa-eye"></i>33357</p>
                                    <p><i class="fa fa-heart"></i>33357</p>
                                </div>
                            </div>
                        </div>
                    </div>
                                    <div class="col oneVideo">
                        <div class="card h-100">
                            <div class="oneVideo-top">
                                <a href="/video?hid=99-21-55995">
                                    <img src="https://airav.io/storage/cover/big/99-21-55995.jpg?1769156308" class="card-img-top" alt="..." onerror="changeImageSrc(this)">
                                    
                                </a>
                            </div>
                            <div class="oneVideo-body">
                                <h5>DSD-854 金髪美女抽插精選！3</h5>
                                <div class="oneVideo-fotter">
                                    <p><i class="fa fa-eye"></i>12858</p>
                                    <p><i class="fa fa-heart"></i>12858</p>
                                </div>
                            </div>
                        </div>
                    </div>
        </div>
    </body></html>
    """
    tree = etree.fromstring(html, etree.HTMLParser())
    parser = Airav()
    parser.init()

    monkeypatch.setattr(parser, "getHtmlTree", lambda *_args, **_kwargs: tree)

    assert (
        parser.queryNumberUrl("DASD-854") == "https://airav.io/video?hid=110394"
    )
