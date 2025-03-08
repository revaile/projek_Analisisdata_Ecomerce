import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
import urllib
import matplotlib.image as mpimg

# Load Data
df_all = pd.read_csv('all_data.csv')
df_geolocation = pd.read_csv('geolocation_dataset.csv')

df_all['order_approved_at'] = pd.to_datetime(df_all['order_approved_at'])

def pertanyaan_satu(df):
    return df.groupby('product_category_name_english')['product_id'].count().reset_index().sort_values(by='product_id', ascending=False)

def pertanyaan_dua(df):
    rating_service = df['review_score'].value_counts().sort_values(ascending=False)
    return rating_service, rating_service.idxmax(), df['review_score'], rating_service.reset_index().rename(columns={'index': 'review_score', 'review_score': 'frequency'})

def pertanyaan_tiga(df):
    df_bulanan = df.resample('M', on='order_approved_at').agg({'order_id': 'nunique'}).reset_index()
    df_bulanan['order_approved_at'] = df_bulanan['order_approved_at'].dt.strftime('%Y-%B')
    return df_bulanan.rename(columns={'order_id': 'order_count'})

def pertanyaan_lima(df1, df2):
    geolocation_map = df1.groupby(['geolocation_zip_code_prefix','geolocation_city','geolocation_state'])[['geolocation_lat','geolocation_lng']].median().reset_index()
    return df2.merge(geolocation_map, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix', how='inner')

df_performa = pertanyaan_tiga(df_all)
pertanyaanSatu = pertanyaan_satu(df_all)
rating_service, max_score, df_rating_service, rating_df = pertanyaan_dua(df_all)
customers_geolocation_map = pertanyaan_lima(df_geolocation, df_all)

st.title('📊 Proyek Analisis Data: E-Commerce Public Dataset')
st.markdown("---")

# PERTAMA
st.subheader("📦 Produk dengan Permintaan Tertinggi & Terendah")
col1, col2 = st.columns(2)
col1.metric("Produk Terbanyak", pertanyaanSatu['product_id'].max())
col2.metric("Produk Tersedikit", pertanyaanSatu['product_id'].min())

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 8))
colors_positive = ["#40E65F", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
colors_negative = ["#D63341", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sorted_new = pertanyaanSatu.sort_values(by="product_id", ascending=False).head(5)
sns.barplot(x="product_id", y="product_category_name_english", 
    data=pertanyaanSatu.sort_values(by="product_id", ascending=False).head(5), 
    palette=colors_positive, hue="product_id",  
    hue_order=sorted(sorted_new['product_id'], reverse=True),
    ax=ax[0])
ax[0].set_xlabel('Frekuensi')
ax[0].set_ylabel('Nama Produk')
ax[0].set_xlabel(None)
ax[0].set_title("Produk dengan jumlah pembelian terbesar", loc="center", fontsize=18)
ax[0].tick_params(axis ='y', labelsize=15)

sns.barplot(x="product_id", y="product_category_name_english", data=pertanyaanSatu.sort_values(by="product_id", ascending=True).head(5), 
    palette=colors_negative, hue="product_id", ax=ax[1])
ax[1].set_xlabel('Frekuensi')
ax[1].set_ylabel('Nama Produk')
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Produk dengan jumlah pembelian terkecil", loc="center", fontsize=18)
ax[1].tick_params(axis='y', labelsize=15)

plt.suptitle("Produk yang memiliki jumlah pembelian terbesar dan terkecil", fontsize=20)
st.pyplot(fig)

st.markdown("Produk **bed_bath_table** memiliki tingkat permintaan tertinggi, sedangkan **security_and_services** memiliki permintaan terendah.")

st.markdown("---")

# KEDUA
# KEDUA
st.subheader('📈 Tren Jumlah Pesanan per Bulan')

# Mendapatkan rentang tanggal dari dataset
min_date = df_all['order_approved_at'].min().date()
max_date = df_all['order_approved_at'].max().date()

# Widget untuk memilih rentang tanggal dengan tampilan lebih nyaman
st.subheader("📅 Pilih Rentang Waktu")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Dari Tanggal", min_date, min_value=min_date, max_value=max_date)
with col2:
    end_date = st.date_input("Sampai Tanggal", max_date, min_value=min_date, max_value=max_date)

# Validasi input agar tanggal awal tidak melebihi tanggal akhir
if start_date > end_date:
    st.warning("⚠️ Tanggal awal tidak boleh lebih besar dari tanggal akhir. Harap pilih ulang rentang tanggal.")
else:
    # Konversi ke datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filter data berdasarkan rentang tanggal
    df_filtered = df_performa[(pd.to_datetime(df_performa['order_approved_at']) >= start_date) & 
                              (pd.to_datetime(df_performa['order_approved_at']) <= end_date)]

    # Menampilkan informasi jumlah data setelah filter
    st.write(f"📊 Menampilkan data dari **{start_date.strftime('%d %B %Y')}** hingga **{end_date.strftime('%d %B %Y')}** ({len(df_filtered)} data).")

    # Menampilkan bulan dengan order terbanyak & tersedikit setelah filter
    if not df_filtered.empty:
        col1, col2 = st.columns(2)
        col1.metric("📈 Bulan dengan Order Terbanyak", df_filtered.loc[df_filtered['order_count'].idxmax(), 'order_approved_at'])
        col2.metric("📉 Bulan dengan Order Tersedikit", df_filtered.loc[df_filtered['order_count'].idxmin(), 'order_approved_at'])

        # Plot hasil filter
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df_filtered['order_approved_at'], df_filtered['order_count'], marker='s', linestyle='--', color='crimson', linewidth=2)
        ax.set_xticklabels(df_filtered['order_approved_at'], rotation=45, ha='right')
        ax.set_title('Jumlah Pesanan Tiap Bulan', fontsize=16)
        ax.set_xlabel("Bulan")
        ax.set_ylabel("Jumlah Pesanan")
        ax.grid(True)
        st.pyplot(fig)
    else:
        st.warning("⚠️ Tidak ada data yang sesuai dengan rentang waktu yang dipilih.")


st.markdown("Pesanan meningkat dari Desember 2016 hingga November 2017, puncaknya pada November 2017.")

st.markdown("---")

# PERTANYAAN KETIGA
st.subheader('⭐ Tingkat Kepuasan Pembeli')
rating_service = df_all['review_score'].value_counts().sort_index()
fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(x=rating_service.index, y=rating_service.values, palette=["#40E65F" if score == rating_service.idxmax() else "#D3D3D3" for score in rating_service.index], ax=ax)
ax.set_title("Tingkat Kepuasan Pembeli dari Rating", fontsize=15)
ax.set_xlabel("Rating")
ax.set_ylabel("Jumlah Customer")
for p in ax.patches:
    ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=11, color='black')
st.pyplot(fig)

st.markdown("Rating **5** paling dominan dengan 66.343 pelanggan.")

st.markdown("---")

# PERTANYAAN LIMA
st.subheader("🗺️ Distribusi Pelanggan Berdasarkan Lokasi")

def plot_brazil_map(data):
    brazil = mpimg.imread(urllib.request.urlopen('https://www.mapsland.com/maps/south-america/brazil/map-of-brazil-with-cities-small.jpg'), 'jpg')
    fig, ax = plt.subplots(figsize=(10, 10))
    data.plot(kind="scatter", x="geolocation_lng", y="geolocation_lat", alpha=0.3, s=0.3, c='maroon', ax=ax)
    plt.axis('off')
    plt.imshow(brazil, extent=[-73.98283055, -32.189, -34.4789, 9.6], aspect='auto')
    st.pyplot(fig)

plot_brazil_map(customers_geolocation_map.drop_duplicates(subset='customer_unique_id'))

st.markdown("Pelanggan terbanyak berada di wilayah selatan Brasil, terutama di **Sao Paulo, Rio de Janeiro, dan Parana**.")
st.markdown("---")
st.markdown("© Copyright by Ade Ripaldi Nuralim")