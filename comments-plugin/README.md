# Komentářový plugin procesu ASWI

## Rozšíření šablony
Aby bylo možné pomocí EPC vygenerovat HTML stránky s komentářovým pluginem, je potřeba upravit soubor **common.xsl**. Ten se nachází mezi šablonami EPC v

*\epf-composer-1.5.2-win32\epf-composer\plugins\org.eclipse.epf.publish.layout_1.5.0.v20180517_2101\layout\xsl*.

Zde je potřeba upravit šablonu **copyright** a to tímto způsobem:

```
<xsl:template name="copyright">
	<div>
		<div id="bg"></div>
		<div id="content-comment-rtc-oslc"></div>
	</div>
	<div id="comments-iframe-div"></div>
		<script type="text/javascript">
			window.onload = function(){
				var wrapper = document.getElementById('comments-iframe-div');
				var page_id = document.getElementById('page-guid').getAttribute('value');
				var page_url = encodeURIComponent(window.top.location.href);

				var src = "http://ea6f66e6.ngrok.io?page_id=" + page_id + "&amp;page_url=" + page_url + "";
				
				var comments_frame = document.createElement("iframe");
				comments_frame.setAttribute("src", src);
				comments_frame.setAttribute("width", "100%");
				comments_frame.setAttribute("height", "845px");
				comments_frame.setAttribute("frameBorder", "0");

				wrapper.appendChild(comments_frame);
			};
	</script>
	<script src="{@BackPath}scripts/ContentComment.js" type="text/javascript" language="JavaScript"></script>
	<link rel="stylesheet" type="text/css" href="{@BackPath}css/css/comment.css"></link>
	<script type="text/javascript" language="JavaScript">
		setTimeout('contentComment.init()',500);
	</script>
	<noscript>Please enable JavaScript to view the comments powered by Rational Team Concert.</noscript>
	<xsl:param name="copyright"/>
	<table class="copyright" border="0" cellspacing="0" cellpadding="0">
		<tr>
			<td class="copyright">
				<xsl:value-of disable-output-escaping="yes" select="$copyright"/>
			</td>
		</tr>
	</table>
</xsl:template>
```

Adresa *http://ea6f66e6.ngrok.io* je adresou komentářové aplikace. Pokud se tedy aplikace nachází jinde, je potřeba tuto adresu změnit.

## Nastavení aplikačního serveru
Ke spuštění aplikačního serveru je potřeba mít nainstalovaný *Python 2.7.xx* a moduly *lxml* verze 3.1 a *psycopg2* verze 2.5.4. Ty jsou uvedené v souboru **requirements.txt**. Instalaci lze tedy provést například následujícím příkazem pomocí správce balíčků *pip*:

`pip install -r requirements.txt`

## Konfigurace
Aby se aplikace připojila ke správné databázi a emailovému serveru, je potřeba uvnitř souboru **aswi_comments_service.py** upravit následující konfiguraci:

```
# CONFIGURATION
#-----------------------------------------------
# PORT NUMBER
PORT_NUMBER = 8080
# DB CONNECTION
HOST = "localhost"
DB_NAME = "aswi_comments"
DB_USER = "aswi_admin"
DB_PASSWORD = "aswi_admin"
# EMAIL CONFIGURATION
SMTP_SERVER = "smtp.gmail.com:587"
EMAIL_FROM = "no-replay@email.com"
EMAIL_TO = ['some_email@gmail.com', 'some_email_2@gmail.com']
EMAIL_SER_LOGIN_NAME = "some_email@gmail.com"
EMAIL_SER_LOGIN_PASSWORD = "xxxxx"
#-----------------------------------------------
```

## Databázový server
Je potřeba mít nainstalovanou a nakonfigurovanou databázi *PostgreSQL* verze 9.xxx. Samotné založení uživatele, databáze a tabulky příspěvku lze provést vykonáním příkazů skriptu **db.sql**.

```
CREATE USER aswi_admin WITH SUPERUSER PASSWORD 'aswi_admin';
CREATE DATABASE aswi_comments OWNER aswi_admin;

CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    author VARCHAR NOT NULL,
    create_time TIMESTAMP NOT NULL,
    comment TEXT NOT NULL,
    page_id VARCHAR(256) NOT NULL
);
```

## Spuštění aplikačního serveru
Nyní lze aplikaci spustit pomocí servisy **aswi_comments_service.py** následujícím příkazem:

`python aswi_comments_service.py > some_log_file.txt`

Aplikace naslouchá na portu 8080. Ukončení lze provést stisknutím *CTRL+C* (pokud aplikace běží na popředí) nebo zasláním signálu *SIGINT* (pokud aplikace běží na pozadí).
