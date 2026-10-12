"""Translations for outgoing notification emails.

The recipient notification is rendered in the language the sender picked for
that recipient; the sender confirmation and the (deferred) download
notification use the sender's own interface language, stored on the record.
Everything falls back to English when a language or key is missing.
"""

SUPPORTED_LANGUAGES = ('en', 'fr', 'es', 'de', 'it')
DEFAULT_LANGUAGE = 'en'


def normalize_language(value) -> str:
    """Coerce an arbitrary input to one of SUPPORTED_LANGUAGES.

    Accepts things like 'FR', 'fr-FR', 'en_US'; anything unknown falls back
    to DEFAULT_LANGUAGE. Keep this the single gate so untrusted form values
    never reach the dict lookups below unvalidated.
    """
    if not value:
        return DEFAULT_LANGUAGE
    code = str(value).strip().lower().replace('_', '-').split('-', 1)[0]
    return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


TRANSLATIONS = {
    'en': {
        'btn_download': 'Download files',
        'download_link_label': 'Download link:',
        'file_summary_label': 'File summary:',
        'total_size_word': 'Total size:',
        'footer_sent_via': 'Sent via iTransfer',
        'footer_on_behalf': 'Sent on behalf of {domain}',
        'message_label': 'Message from the sender:',
        'date_at': 'at',
        'recipient_subject': '{sender} sent you files',
        'recipient_title': 'You have received files',
        'recipient_body': '{sender} sent you files. Click the button below to access the download page.',
        'expiry_line': 'This link will expire on {date}',
        'sender_subject': 'Transfer confirmation to {recipient}',
        'sender_title': 'Your files have been sent',
        'sender_body': 'Your files have been sent to: {recipient}',
        'sender_download_page': 'Download page: {link}',
        'download_subject': 'Your files have been downloaded',
        'download_title': 'Your files have been downloaded',
        'download_body': 'Your files were downloaded on {datetime}.',
        'smtp_test_subject': 'SMTP configuration test',
        'smtp_test_body': 'iTransfer SMTP test.',
    },
    'fr': {
        'btn_download': 'Télécharger les fichiers',
        'download_link_label': 'Lien de téléchargement :',
        'file_summary_label': 'Détail des fichiers :',
        'total_size_word': 'Taille totale :',
        'footer_sent_via': 'Envoyé via iTransfer',
        'footer_on_behalf': 'Envoyé pour le compte de {domain}',
        'message_label': "Message de l'expéditeur :",
        'date_at': 'à',
        'recipient_subject': '{sender} vous a envoyé des fichiers',
        'recipient_title': 'Vous avez reçu des fichiers',
        'recipient_body': '{sender} vous a envoyé des fichiers. Cliquez sur le bouton ci-dessous pour accéder à la page de téléchargement.',
        'expiry_line': 'Ce lien expirera le {date}',
        'sender_subject': "Confirmation d'envoi à {recipient}",
        'sender_title': 'Vos fichiers ont été envoyés',
        'sender_body': 'Vos fichiers ont été envoyés à : {recipient}',
        'sender_download_page': 'Page de téléchargement : {link}',
        'download_subject': 'Vos fichiers ont été téléchargés',
        'download_title': 'Vos fichiers ont été téléchargés',
        'download_body': 'Vos fichiers ont été téléchargés le {datetime}.',
        'smtp_test_subject': 'Test de configuration SMTP',
        'smtp_test_body': 'Test SMTP iTransfer.',
    },
    'es': {
        'btn_download': 'Descargar archivos',
        'download_link_label': 'Enlace de descarga:',
        'file_summary_label': 'Resumen de archivos:',
        'total_size_word': 'Tamaño total:',
        'footer_sent_via': 'Enviado mediante iTransfer',
        'footer_on_behalf': 'Enviado en nombre de {domain}',
        'message_label': 'Mensaje del remitente:',
        'date_at': 'a las',
        'recipient_subject': '{sender} te ha enviado archivos',
        'recipient_title': 'Has recibido archivos',
        'recipient_body': '{sender} te ha enviado archivos. Haz clic en el botón de abajo para acceder a la página de descarga.',
        'expiry_line': 'Este enlace caducará el {date}',
        'sender_subject': 'Confirmación de envío a {recipient}',
        'sender_title': 'Tus archivos han sido enviados',
        'sender_body': 'Tus archivos han sido enviados a: {recipient}',
        'sender_download_page': 'Página de descarga: {link}',
        'download_subject': 'Tus archivos han sido descargados',
        'download_title': 'Tus archivos han sido descargados',
        'download_body': 'Tus archivos se descargaron el {datetime}.',
        'smtp_test_subject': 'Prueba de configuración SMTP',
        'smtp_test_body': 'Prueba SMTP de iTransfer.',
    },
    'de': {
        'btn_download': 'Dateien herunterladen',
        'download_link_label': 'Download-Link:',
        'file_summary_label': 'Dateiübersicht:',
        'total_size_word': 'Gesamtgröße:',
        'footer_sent_via': 'Gesendet über iTransfer',
        'footer_on_behalf': 'Gesendet im Auftrag von {domain}',
        'message_label': 'Nachricht vom Absender:',
        'date_at': 'um',
        'recipient_subject': '{sender} hat Ihnen Dateien gesendet',
        'recipient_title': 'Sie haben Dateien erhalten',
        'recipient_body': '{sender} hat Ihnen Dateien gesendet. Klicken Sie auf die Schaltfläche unten, um zur Download-Seite zu gelangen.',
        'expiry_line': 'Dieser Link läuft am {date} ab',
        'sender_subject': 'Versandbestätigung an {recipient}',
        'sender_title': 'Ihre Dateien wurden gesendet',
        'sender_body': 'Ihre Dateien wurden gesendet an: {recipient}',
        'sender_download_page': 'Download-Seite: {link}',
        'download_subject': 'Ihre Dateien wurden heruntergeladen',
        'download_title': 'Ihre Dateien wurden heruntergeladen',
        'download_body': 'Ihre Dateien wurden am {datetime} heruntergeladen.',
        'smtp_test_subject': 'SMTP-Konfigurationstest',
        'smtp_test_body': 'iTransfer SMTP-Test.',
    },
    'it': {
        'btn_download': 'Scarica i file',
        'download_link_label': 'Link per il download:',
        'file_summary_label': 'Riepilogo file:',
        'total_size_word': 'Dimensione totale:',
        'footer_sent_via': 'Inviato tramite iTransfer',
        'footer_on_behalf': 'Inviato per conto di {domain}',
        'message_label': 'Messaggio dal mittente:',
        'date_at': 'alle',
        'recipient_subject': '{sender} ti ha inviato dei file',
        'recipient_title': 'Hai ricevuto dei file',
        'recipient_body': '{sender} ti ha inviato dei file. Clicca sul pulsante qui sotto per accedere alla pagina di download.',
        'expiry_line': 'Questo link scadrà il {date}',
        'sender_subject': 'Conferma di invio a {recipient}',
        'sender_title': 'I tuoi file sono stati inviati',
        'sender_body': 'I tuoi file sono stati inviati a: {recipient}',
        'sender_download_page': 'Pagina di download: {link}',
        'download_subject': 'I tuoi file sono stati scaricati',
        'download_title': 'I tuoi file sono stati scaricati',
        'download_body': 'I tuoi file sono stati scaricati il {datetime}.',
        'smtp_test_subject': 'Test di configurazione SMTP',
        'smtp_test_body': 'Test SMTP di iTransfer.',
    },
}


def t(lang, key, **kwargs) -> str:
    """Translate `key` into `lang`, falling back to English per missing key.

    `lang` is normalized here too so callers may pass a raw value safely.
    """
    lang = normalize_language(lang)
    table = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE])
    template = table.get(key) or TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    try:
        return template.format(**kwargs) if kwargs else template
    except (KeyError, IndexError):
        return template
