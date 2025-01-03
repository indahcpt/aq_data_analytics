import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sn

from geopy.geocoders import Nominatim
import time

import geopandas as gpd
from shapely.geometry import Point

import folium
from folium.plugins import MarkerCluster, HeatMap
from IPython.display import display

import streamlit as st
import streamlit.components.v1 as components

sn.set(style='dark')

# Helper function yang dibutuhkan untuk menyiapkan berbagai dataframe



# Menghitung jumlah stasiun, rata-rata partikel padat dan gas per stasiun
def create_prsa_avg_df(prsa_df):
    # Menghitung jumlah unik stasiun dan rata-rata keseluruhan untuk setiap kolom
    total_unique_stations = prsa_df['station'].nunique()
    avg_all_data = prsa_df[['PM2.5', 'PM10', 'CO', 'SO2', 'NO2', 'O3']].mean()

    prsa_avg_df = pd.DataFrame({
        'station_count': [total_unique_stations], 
        'avg_PM2_5': [avg_all_data['PM2.5']], 
        'avg_PM10': [avg_all_data['PM10']], 
        'avg_CO': [avg_all_data['CO']], 
        'avg_SO2': [avg_all_data['SO2']], 
        'avg_NO2': [avg_all_data['NO2']], 
        'avg_O3': [avg_all_data['O3']]
    })
    return prsa_avg_df

def create_prsa_debu_allyear_df(prsa_df):
    prsa_debu_allyear_df = prsa_df.groupby(["station"]).agg({
    "PM2.5": "mean",
    "PM10": "mean"
    }).sort_values(by=[("PM2.5"), ("PM10")], ascending=False).reset_index()

    return prsa_debu_allyear_df

def create_prsa_debu_hourly_df(prsa_df):
    prsa_debu_hourly_df = prsa_df.groupby(["hour"]).agg({
    "PM2.5": "mean",
    "PM10": "mean"
    }).reset_index()

    return prsa_debu_hourly_df

def create_prsa_debu_station_hourly_df(prsa_df):
    prsa_debu_station_hourly_df = prsa_df.groupby(["station","hour"]).agg({
    "PM2.5": "mean",
    "PM10": "mean"
    }).reset_index()

    return prsa_debu_station_hourly_df


def create_prsa_gas_allyear_df(prsa_df):
    prsa_gas_allyear_df = prsa_df.groupby(by="station").agg({
        "CO": "mean",
        "SO2": "mean",
        "NO2": "mean",
        "O3": "mean"
    }).reset_index()
    
    return prsa_gas_allyear_df


# def create_prsa_debu_cluster_df(prsa_df):
#     prsa_debu_cluster_df = prsa_df.groupby(["station"]).agg({
#     "PM2.5": "mean",
#     "PM10": "mean"
#     }).reset_index()

#     prsa_debu_cluster_df['PM2.5-category'] = pd.qcut(prsa_debu_cluster_df['PM2.5'], q=3, labels=['Rendah', 'Sedang', 'Tinggi'])
#     prsa_debu_cluster_df['PM10-category'] = pd.qcut(prsa_debu_cluster_df['PM10'], q=3, labels=['Rendah', 'Sedang', 'Tinggi'])


#     return prsa_debu_cluster_df

def create_prsa_debu_cluster_df(prsa_df):
    prsa_debu_cluster_df = prsa_df.groupby(["station"]).agg({
    "PM2.5": "mean",
    "PM10": "mean"
    }).reset_index()

    # Menentukan kategori PM2.5
    bins_pm25 = [0, 70, 85, float('inf')]  # Batas-batas nilai PM2.5
    labels_pm25 = ['Rendah', 'Sedang', 'Tinggi']
    prsa_debu_cluster_df['PM2.5-category'] = pd.cut(prsa_debu_cluster_df['PM2.5'], bins=bins_pm25, labels=labels_pm25, right=False)

    # Menentukan kategori PM10
    bins_pm10 = [0, 90, 110, float('inf')]  # Batas-batas nilai PM10
    labels_pm10 = ['Rendah', 'Sedang', 'Tinggi']
    prsa_debu_cluster_df['PM10-category'] = pd.cut(prsa_debu_cluster_df['PM10'], bins=bins_pm10, labels=labels_pm10, right=False)

    return prsa_debu_cluster_df



def create_prsa_pm25_cluster_df(prsa_debu_cluster_df):
    prsa_pm25_cluster_df = prsa_debu_cluster_df.groupby(by="PM2.5-category").index.nunique().reset_index()
    prsa_pm25_cluster_df.rename(columns={
            "index": "station_count"
        }, inplace=True)
    
    return prsa_pm25_cluster_df

def create_prsa_pm10_cluster_df(prsa_debu_cluster_df):
    prsa_pm10_cluster_df = prsa_debu_cluster_df.groupby(by="PM10-category").index.nunique().reset_index()
    prsa_pm10_cluster_df.rename(columns={
            "index": "station_count"
        }, inplace=True)
    
    return prsa_pm10_cluster_df

# Menghitung rata-rata PM2.5 dan PM10 per station
def create_pm_geo_df(prsa_df):
    pm_geo_df = prsa_df.groupby(['station', 'latitude', 'longitude', 'geometry'], as_index=False).agg({
        'PM2.5': 'mean',
        'PM10': 'mean'
    })
    return pm_geo_df


# Load cleaned data
all_df = pd.read_csv("all_data_cleaned.csv")

all_df['date'] = pd.to_datetime(all_df[['year', 'month', 'day']])

datetime_columns = ["date"]
all_df.sort_values(by="date", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

# Filter data
min_date = all_df["date"].min()
max_date = all_df["date"].max()

with st.sidebar:
    # Menambahkan logo perusahaan
    
    st.image("https://pict.sindonews.net/dyn/732/pena/news/2022/06/23/207/806513/5-aplikasi-cek-kualitas-udara-terbaik-untuk-pengguna-android-maupun-ios-ufp.jpg")
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

    # Filter nama stasiun
    stations = ['Semua Stasiun'] + list(all_df["station"].unique())  # Mengambil nama stasiun unik
    selected_station = st.selectbox("Pilih Stasiun", stations)

# Memfilter data berdasarkan tanggal dan stasiun yang dipilih
if selected_station == "Semua Stasiun":
    main_df = all_df[(all_df["date"] >= pd.to_datetime(start_date)) & 
                     (all_df["date"] <= pd.to_datetime(end_date))]
else:
    main_df = all_df[(all_df["date"] >= pd.to_datetime(start_date)) & 
                     (all_df["date"] <= pd.to_datetime(end_date)) & 
                     (all_df["station"] == selected_station)]



# Menyiapkan berbagai dataframe
prsa_avg_df = create_prsa_avg_df(main_df)
prsa_debu_allyear_df = create_prsa_debu_allyear_df(main_df)
prsa_debu_hourly_df = create_prsa_debu_hourly_df(main_df)
prsa_debu_station_hourly_df = create_prsa_debu_station_hourly_df(main_df)
prsa_gas_allyear_df = create_prsa_gas_allyear_df(main_df)
prsa_debu_cluster_df = create_prsa_debu_cluster_df(main_df).reset_index()
prsa_pm25_cluster_df =  create_prsa_pm25_cluster_df(prsa_debu_cluster_df)
prsa_pm10_cluster_df = create_prsa_pm10_cluster_df(prsa_debu_cluster_df)
pm_geo_df = create_pm_geo_df(main_df)


# plot number of daily orders (2021)
st.header('Dashboard Kualitas Udara')
# Menampilkan data yang telah difilter
st.markdown(f"**Data untuk Stasiun: {selected_station} dari {start_date} hingga {end_date}**")


# Membuat 3 kolom untuk menampilkan metrik secara dinamis
columns = ['station_count', 'avg_PM2_5', 'avg_PM10','']

# Membuat 7 kolom secara dinamis 
cols = st.columns(4)  

# Menampilkan metrik pada setiap kolom
for i, col in enumerate(columns):
    if col:  # Mengecek jika kolom tidak kosong
        col_label = col.replace('_', ' ').title()  # Menyusun label kolom yang lebih rapi
        cols[i].metric(col_label, value=round(prsa_avg_df[col][0], 2))
    else:
        cols[i].empty()  # Kolom ke-empat kosong
# Membuat 4 kolom untuk menampilkan metrik secara dinamis
columns = ['avg_CO', 'avg_SO2', 'avg_NO2', 'avg_O3']

# Membuat 4 kolom secara dinamis 
cols = st.columns(4)  

# Menampilkan metrik pada setiap kolom
for i, col in enumerate(columns):
    col_label = col.replace('_', ' ').title()  # Menyusun label kolom yang lebih rapi
    cols[i].metric(col_label, value=round(prsa_avg_df[col][0], 2))


# Partikel Padat per Stasiun
st.markdown('##### **PM2.5 dan PM10 per Stasiun**')
fig, ax = plt.subplots(figsize=(16, 8))
bar_width = 0.35
index = range(len(prsa_debu_allyear_df['station']))

# Plot PM2.5 dan PM10
bar1 = ax.barh(index, prsa_debu_allyear_df['PM2.5'], bar_width, label='PM2.5', color='skyblue')
bar2 = ax.barh([i + bar_width for i in index], prsa_debu_allyear_df['PM10'], bar_width, label='PM10', color='salmon')

# Menambahkan label
ax.set_ylabel('Stasiun')
ax.set_xlabel('Konsentrasi (µg/m³)')
ax.set_title('Konsentrasi PM2.5 dan PM10 di Berbagai Stasiun')
ax.set_yticks([i + bar_width / 2 for i in index])
ax.set_yticklabels(prsa_debu_allyear_df['station'])
ax.legend()

st.pyplot(fig)



# Partikel Debu Per Jam
st.markdown('##### **Rata-rata Konsentrasi PM2.5 dan PM10 Per Jam**')

# Membuat grafik
fig, ax = plt.subplots(figsize=(16, 8))

# Plot untuk PM2.5
ax.plot(
    prsa_debu_hourly_df["hour"],
    prsa_debu_hourly_df["PM2.5"],
    marker='o', 
    linewidth=2,
    color="#90CAF9",
    label="PM2.5"  # Menambahkan label untuk legend
)

# Plot untuk PM10
ax.plot(
    prsa_debu_hourly_df["hour"],
    prsa_debu_hourly_df["PM10"],
    marker='s', 
    linewidth=2,
    color="#FF8A80",
    label="PM10"  # Menambahkan label untuk legend
)

# Menambahkan label dan judul
ax.set_xlabel("Jam", fontsize=15)
ax.set_ylabel("Konsentrasi (µg/m³)", fontsize=15)
ax.set_title("Konsentrasi PM2.5 dan PM10 Per Jam", fontsize=20)

# Menambahkan grid dan legend
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend(fontsize=15)

# Mengatur ukuran label sumbu
ax.tick_params(axis='y', labelsize=15)
ax.tick_params(axis='x', labelsize=15)

# Menampilkan grafik di Streamlit
st.pyplot(fig)


# Partikel Debu Tiap Jam Per Stasiun
# Membuat dua kolom untuk tata letak horizontal
col1, col2 = st.columns(2)

# === Grafik PM2.5 ===
with col1:
    st.markdown('##### **PM2.5 Per Jam Per Stasiun**')
    
    # Membuat grafik
    fig, ax = plt.subplots(figsize=(7, 6))  # Ukuran grafik lebih kecil agar pas di kolom
    
    # Plot untuk PM2.5 per stasiun
    for station in prsa_debu_station_hourly_df["station"].unique():
        data_station = prsa_debu_station_hourly_df[prsa_debu_station_hourly_df["station"] == station]
        ax.plot(
            data_station["hour"],  # Sumbu X
            data_station["PM2.5"],  # Sumbu Y
            label=station  # Menambahkan label untuk legenda
        )
    
    # Konfigurasi grafik
    ax.set_xlabel("Waktu (Jam)", fontsize=10)
    ax.set_ylabel("Konsentrasi (µg/m³)", fontsize=10)
    ax.set_title("PM2.5", fontsize=12)
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.set_xticks(range(0, 24))
    ax.tick_params(axis='x', rotation=45)

    # Menampilkan grafik di Streamlit
    st.pyplot(fig)

# === Grafik PM10 ===
with col2:
    st.markdown('##### **PM10 Per Jam Per Stasiun**')
    # Membuat grafik
    fig, ax = plt.subplots(figsize=(7, 6))  # Ukuran grafik lebih kecil agar pas di kolom
    
    # Plot untuk PM10 per stasiun
    for station in prsa_debu_station_hourly_df["station"].unique():
        data_station = prsa_debu_station_hourly_df[prsa_debu_station_hourly_df["station"] == station]
        ax.plot(
            data_station["hour"],  # Sumbu X
            data_station["PM10"],  # Sumbu Y
            label=station  # Menambahkan label untuk legenda
        )
    
    # Konfigurasi grafik
    ax.set_xlabel("Waktu (Jam)", fontsize=10)
    ax.set_ylabel("Konsentrasi (µg/m³)", fontsize=10)
    ax.set_title("PM10", fontsize=12)
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.set_xticks(range(0, 24))
    ax.tick_params(axis='x', rotation=45)

    # Menampilkan grafik di Streamlit
    st.pyplot(fig)


# Partikel Padat per Stasiun

#st.subheader('Gas CO per Stasiun')
st.markdown('##### **Gas CO per Stasiun**')
# Membuat figure dan axes
fig, ax = plt.subplots(figsize=(16, 8))
bar_width = 0.8  # Lebar bar

# Mengatur posisi indeks sesuai jumlah data
index = range(len(prsa_gas_allyear_df['station']))

# Plot CO dengan bar horizontal
bar = ax.barh(index, 
            prsa_gas_allyear_df['CO'], 
            height=bar_width, 
            label='CO', 
            color='skyblue')

# Menambahkan label dan judul
ax.set_xlabel('Konsentrasi (µg/m³)')
ax.set_ylabel('Stasiun')
ax.set_title('Konsentrasi Gas CO di Berbagai Stasiun')

# Mengatur label sumbu Y sesuai urutan data
ax.set_yticks(index)
ax.set_yticklabels(prsa_gas_allyear_df['station'])  # Sesuai nama stasiun

# Menambahkan grid untuk memperjelas tampilan
ax.grid(axis='x', linestyle='--', alpha=0.6)

# Menampilkan grafik di halaman Streamlit
st.pyplot(fig)


#st.subheader('Gas SO2, NO2 dan O3 per Stasiun')
st.markdown('##### **Gas SO2, NO2 dan O3 per Stasiun**')

fig, ax = plt.subplots(figsize=(16, 8))
bar_width = 0.25
index = range(len(prsa_gas_allyear_df['station']))

# Plot PM2.5 dan PM10
bar1 = ax.barh(index, prsa_gas_allyear_df['SO2'], bar_width, label='SO2', color='#001F3F')
bar2 = ax.barh([i + bar_width for i in index], prsa_gas_allyear_df['NO2'], bar_width, label='NO2', color='skyblue')
bar3 = ax.barh([i + 2*bar_width for i in index], prsa_gas_allyear_df['O3'], bar_width, label='O3', color='salmon')

# Menambahkan label
ax.set_ylabel('Stasiun')
ax.set_xlabel('Konsentrasi (µg/m³)')
ax.set_title('Konsentrasi SO2, NO2 dan O3 di Berbagai Stasiun')
ax.set_yticks([i + bar_width / 2 for i in index])
ax.set_yticklabels(prsa_gas_allyear_df['station'])
ax.legend()

st.pyplot(fig)

# Pie Chart Klasterisasi Stasiun Berdasarkan PM2.5 dan PM10
col1, col2 = st.columns(2)

# === Grafik PM2.5 ===
with col1:
    st.markdown('##### **Stasiun per Kategori PM2.5**')
    # Menghitung jumlah stasiun per kategori PM2.5
    category_counts = prsa_pm25_cluster_df.set_index("PM2.5-category")['station_count']

    # Membuat pie chart
    fig, ax = plt.subplots(figsize=(8, 8))
    category_counts.plot(kind='pie', autopct='%1.1f%%', startangle=90, legend=False, ax=ax)
    #ax.set_title('Stasiun per Kategori PM2.5')
    ax.set_ylabel('')  # Menghapus label 'PM2.5-category' yang tidak perlu

    # Menampilkan pie chart di Streamlit
    st.pyplot(fig)

# === Grafik PM2.5 ===
with col2:
    st.markdown('##### **Stasiun per Kategori PM10**')
    # Menghitung jumlah stasiun per kategori PM10
    category_counts = prsa_pm10_cluster_df.set_index("PM10-category")['station_count']

    # Membuat pie chart
    fig, ax = plt.subplots(figsize=(8, 8))
    category_counts.plot(kind='pie', autopct='%1.1f%%', startangle=90, legend=False, ax=ax)
    #ax.set_title('Stasiun per Kategori PM10')
    ax.set_ylabel('')  # Menghapus label 'PM2.5-category' yang tidak perlu

    # Menampilkan pie chart di Streamlit
    st.pyplot(fig)

# Heatmap PM2.5 dan PM10 per Stasiun
st.markdown('##### **Heatmap PM2.5 dan PM10 Per Stasiun**')

# Membuat peta dasar di koordinat tengah dari dataset
peta = folium.Map(location=[pm_geo_df['latitude'].mean(), pm_geo_df['longitude'].mean()], zoom_start=6)

# Menambahkan MarkerCluster untuk stasiun
marker_cluster = MarkerCluster().add_to(peta)

# Menambahkan marker untuk setiap stasiun dengan popup yang menampilkan PM2.5 dan PM10
for _, row in pm_geo_df.iterrows():
    folium.Marker([row['latitude'], row['longitude']], 
                  popup=f"{row['station']}: PM2.5 = {row['PM2.5']} µg/m³, PM10 = {row['PM10']} µg/m³").add_to(marker_cluster)

# Menambahkan heatmap berdasarkan nilai PM2.5
heat_data = [[row['latitude'], row['longitude'], row['PM2.5']] for index, row in pm_geo_df.iterrows()]
HeatMap(heat_data, cmap='coolwarm', radius=15).add_to(peta)

# Menampilkan peta dalam Streamlit
components.html(peta._repr_html_(), height=600)

st.caption('Copyright © Dicoding 2023')