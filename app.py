import pandas as pd
import streamlit as st
import io
import numpy as np

st.title("Dosya Maskeleme Modülü")

st.markdown(
    """
    <style>
    .main {
        background-color: #002b36; 
        padding: 20px;
        border-radius: 10px;
    }
    .stApp {
        background-color: #002b36;
        background-image: linear-gradient(315deg, #fafafa 0%, #586e75 74%);
        color: #d33682;
    }
    .title {
        font-family: 'Arial', sans-serif;
        text-align: center;
        font-size: 30px;
        color: #fafafa;
    }
    .file-upload {
        margin: 20px 0;
        color: #fafafa;
    }
    .download-button {
        margin-top: 20px;
        color: #fafafa;
    }
    /* Dosya yükleyici bileşeninin stilini değiştir */
    .stFileUpload > label, .stFileUpload > div {
        color: #fafafa; /* Metin rengi */
    }
    /* Çoklu seçim bileşeni için stil */
    .stMultiSelect label, .stMultiSelect div {
        color: #fafafa; /* Metin rengi */
    }
    .fixed-text-right {
        position: fixed;
        bottom: 10px;
        right: 10px;
        font-size: 14px;
        color: #fafafa;
        background-color: #586e75;
        padding: 5px 10px;
        border-radius: 5px;
        font-family: 'Arial', sans-serif;
        z-index: 9999;
    }
    .fixed-text-left {
        position: fixed;
        bottom: 10px;
        left: 10px;
        font-size: 14px;
        color: #fafafa;
        background-color: #586e75;
        padding: 5px 10px;
        border-radius: 5px;
        font-family: 'Arial', sans-serif;
        z-index: 9999;
    }
    </style>

    <div class="fixed-text-right">Kızılaykart Bilgi Yönetimi</div>
    <div class="fixed-text-left">Batuhan Aydın</div>
    """,
    unsafe_allow_html=True
)



uploaded_file = st.file_uploader("Bir Excel dosyası yükleyin", type="xlsx")

if uploaded_file is not None:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names
    
    if len(sheet_names) > 1:
        # Kullanıcıdan bir sayfa seçmesini iste
        selected_sheet = st.selectbox("Çalışmak istediğiniz sayfayı seçin", sheet_names)
    else:
        # Yalnızca bir sayfa varsa onu seç
        selected_sheet = sheet_names[0]

    # Seçilen sayfayı yükle
    df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
    filtered_df = df.copy()
    
    def detect_column_by_pattern(df):
        for column in df.columns:
            if df[column].apply(lambda x: (pd.isna(x)) or (isinstance(x, int) and len(str(x)) == 11)).all():
                return column
        return None
    
    def detect_kartno_by_pattern(df_caller):
        
        for column in df.columns:
            if column == "KartNo":
                df_caller = df.dropna(subset=['KartNo'])
                df_caller['A_str'] = df_caller[column].apply(lambda x: format(x, '.0f'))
                if df_caller['A_str'].apply(lambda x: len(x) == 16).all():
                    df[column].fillna("0000000000000000", inplace=True)
                    df[column] = df_caller[column].astype(str).replace("\.0", "", regex=True)
                    return column
        return None

    def detect_name_columns(df):
        ad_keywords = ['AD', 'Ad', 'ad', 'ADI', 'Adı', 'adı', 'İsim' ,'isim']
        soyad_keywords = ['SOYAD', 'Soyad', 'soyad', 'SOYADI', 'Soyadı', 'soyadı', 'Soy isim', 'soyisim', 'soy_isim']
        
        ad_column = None
        soyad_column = None
        
        for column in df.columns:
            if column in ad_keywords:
                ad_column = column
            elif column in soyad_keywords:
                soyad_column = column
        
        
        return ad_column, soyad_column

    def mask_name(name):
        if pd.isna(name):  # NaN veya None kontrolü
            return name
        masked_parts = []
        for part in name.split():
            if len(part) > 2:
                masked_part = part[:2] + '*' * (len(part) - 2)
            else:
                masked_part = part
            masked_parts.append(masked_part)
        return ' '.join(masked_parts)



    detected_YKN = detect_column_by_pattern(filtered_df)
    detected_Kart = detect_kartno_by_pattern(filtered_df)
    detected_ad, detected_soyad = detect_name_columns(filtered_df)
    
    detected_columns = []
    
    if detected_YKN is not None:
        detected_columns.append(detected_YKN)
    if detected_Kart is not None:
        detected_columns.append(detected_Kart)
    if detected_ad is not None:
        detected_columns.append(detected_ad)
    if detected_soyad is not None:
        detected_columns.append(detected_soyad)

    # Tüm tespit edilen sütunları varsayılan olarak seçili göstermek için:
    columns_to_filter = st.multiselect("Maskelenecek sütunları seçin", detected_columns, default=detected_columns)

    # Kullanıcının seçimine göre işlemleri gerçekleştirme
    if detected_YKN is not None and detected_YKN in columns_to_filter:
        df[detected_YKN] = df[detected_YKN].dropna().astype(np.int64)
        df[detected_YKN] = df[detected_YKN].dropna().astype(str).replace('\.0', '', regex=True)
        df[detected_YKN] = df[detected_YKN].str[0:3] + "*****" + df[detected_YKN].str[-3:]

    if detected_Kart is not None and detected_Kart in columns_to_filter:
        df[detected_Kart] = df[detected_Kart].str[0:4] + " **** **** " + df[detected_Kart].str[-4:]
        df[detected_Kart].replace("0000 **** **** 0000", np.nan, inplace=True)

    if detected_ad is not None and detected_ad in columns_to_filter:
        df[detected_ad] = df[detected_ad].apply(mask_name)

    if detected_soyad is not None and detected_soyad in columns_to_filter:
        df[detected_soyad] = df[detected_soyad].apply(mask_name)
   
                
    xlsx_io = io.BytesIO()
    with pd.ExcelWriter(xlsx_io, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)

    xlsx_io.seek(0)
    st.download_button(
        label="Maskelenmiş verileri Excel olarak indir",
        data=xlsx_io,
        file_name='filtered_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                )
        
