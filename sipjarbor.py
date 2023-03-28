import streamlit as st
import pandas as pd
import datetime
import altair as alt
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
import locale
import os
import mysql.connector
import plotly.graph_objs as go
import json
import urllib.parse
import webbrowser
from mysql.connector import Error
# import pywhatkit as kit
import folium
from streamlit_folium import folium_static

# Fungsi untuk login
def login():
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        # validasi login
        if username == "admin" and password == "admin123":
            session_state.logged_in = True
            session_state.user_type = "admin"
            st.success("Login berhasil!")
        elif username == "user" and password == "user123":
            session_state.logged_in = True
            session_state.user_type = "user"
            st.success("Login berhasil!")
        else:
            st.error("Invalid username or password")

# Fungsi untuk menampilkan halaman home (Page 1)
def home():
    # Load env variables
    # load_dotenv()

    # Set locale ke bahasa Indonesia dan format uang Rupiah
    # locale.setlocale(locale.LC_ALL, 'id_ID')

    # Menghubungkan dengan secrets streamlit share
    DB_HOST = st.secrets["sql"]["DB_HOST"]
    DB_PORT = st.secrets["sql"]["DB_PORT"]
    DB_DATABASE = st.secrets["sql"]["DB_DATABASE"]
    DB_USERNAME = st.secrets["sql"]["DB_USERNAME"]
    DB_PASSWORD = st.secrets["sql"]["DB_PASSWORD"]
    
    # Koneksi ke database
    mydb = mysql.connector.connect(
   
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USERNAME,
        password=DB_PASSWORD,
        database=DB_DATABASE

    )
    cursor = mydb.cursor()


    # Membaca data dari tabel pendapatan_sw di database
    cursor.execute("SELECT * FROM tb_pendapatan34")
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["NO", "TANGGAL", "LOKET", "KD", "SW", "DENDA", "TOTAL"])

    # Tampilkan tanggal terakhir data diperbaharui
    last_update = df['TANGGAL'].max().strftime('%d %B %Y')
    st.write(f"Data terakhir diperbaharui pada {last_update}")

    # Menampilkan data visual berupa perhitungan hasil pendapatan
    st.title('Dashboard Analytics')
    st.subheader('SIPJARBOR')

    # Load data dari tabel pendapatan_sw di database dan ubah tipe data kolom TANGGAL menjadi datetime
    cursor.execute("SELECT * FROM tb_pendapatan34")
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["NO", "TANGGAL", "LOKET", "KD", "SW", "DENDA", "TOTAL"])
    df['TANGGAL'] = pd.to_datetime(df['TANGGAL'])


    # Buat sidebar dengan widget untuk memilih rentang tanggal dan filter LOKET:
    start_date = st.sidebar.date_input("Start date", datetime.date(2023, 1, 1), min_value=df['TANGGAL'].min().date(), max_value=df['TANGGAL'].max().date())
    end_date = st.sidebar.date_input("End date", df['TANGGAL'].max().date(), min_value=start_date, max_value=df['TANGGAL'].max().date())

    loket_list = df['LOKET'].unique().tolist()

    # Tambahkan 'Perwakilan Bogor' ke dalam loket_list
    loket_list.append('Perwakilan Bogor')

    # Buat sidebar untuk memilih loket dan tambahkan tombol 'Perwakilan Bogor'
    with st.sidebar:
        selected_loket = st.sidebar.multiselect("Select LOKET", loket_list, default=loket_list)
        if st.sidebar.button('Perwakilan Bogor'):
            selected_loket = loket_list[:-1]
            st.sidebar.write('All LOKET are selected')

### Ini koding menampilkan total pendapatan
    # Filter data sesuai rentang tanggal dan LOKET yang dipilih:
    mask = (df['TANGGAL'] >= pd.to_datetime(start_date)) & (df['TANGGAL'] <= pd.to_datetime(end_date)) & (df['LOKET'].isin(selected_loket))
    filtered_df = df.loc[mask]

    # Hitung total KD, SW, DENDA:
    filtered_df['TOTAL'] = filtered_df['KD'] + filtered_df['SW'] + filtered_df['DENDA']
    total_kd = filtered_df['KD'].sum()
    total_sw = filtered_df['SW'].sum()
    total_denda = filtered_df['DENDA'].sum()
    total = total_kd + total_sw + total_denda

 ### Ini koding menghitung aktifitas YOY   
    # Filter data untuk periode yang sama tahun lalu
    start_date_last_year = start_date.replace(year=start_date.year - 1)
    end_date_last_year = end_date.replace(year=end_date.year - 1)
    mask_last_year = (df['TANGGAL'] >= pd.to_datetime(start_date_last_year)) & (df['TANGGAL'] <= pd.to_datetime(end_date_last_year)) & (df['LOKET'].isin(selected_loket))
    filtered_df_last_year = df.loc[mask_last_year]

### Ini koding menghitung aktifitas YOY
    # Hitung aktifitas KD, SW, Denda, dan Total untuk periode yang sama tahun lalu
    aktifitas_kd_last_year = filtered_df_last_year['KD'].sum()
    aktifitas_sw_last_year = filtered_df_last_year['SW'].sum()
    aktifitas_denda_last_year = filtered_df_last_year['DENDA'].sum()
    aktifitas_total_last_year = aktifitas_kd_last_year + aktifitas_sw_last_year + aktifitas_denda_last_year


# Membaca data dari tabel target di database
    cursor.execute("SELECT * FROM tb_target")
    data = cursor.fetchall()
    target_df = pd.DataFrame(data, columns=["NO", "LOKET", "TARGET_KD", "TARGET_SW", "TARGET_DENDA", "TARGET_IW"])


# Membaca target tiap loket
    target_loket = target_df[target_df['LOKET'].isin(selected_loket)]
    target_kd = target_loket['TARGET_KD'].sum()
    target_sw = target_loket['TARGET_SW'].sum()
    target_denda = target_loket['TARGET_DENDA'].sum()

    # Filter data for the selected date range and loket
    start_date_data = datetime.date(2023, 1, 1)
    end_date_data = datetime.date(2023, 12, 31)

    # Filter data for the selected date range and loket
    mask_target = (df['TANGGAL'] >= pd.to_datetime(start_date_data)) & (df['TANGGAL'] <= pd.to_datetime(end_date_data)) & (df['LOKET'].isin(selected_loket))
    filtered_df = df.loc[mask_target]

    # Calculate the percentage of achievement towards the annual target
    realisasi_kd = total_kd / target_kd * 100
    realisasi_sw = total_sw / target_sw * 100
    realisasi_denda = total_denda / target_denda * 100

    # Menggabungkan total pendapatan dan target untuk setiap jenis pendapatan
    target_total = target_kd + target_sw + target_denda
    total_target_df = pd.DataFrame({'TOTAL': [total], 'TARGET': [target_total]})

    # Menghitung nilai realisasi terhadap target untuk keseluruhan pendapatan
    realisasi_total = total / target_total * 100



### Ini koding menghitung aktifitas YOY
    # Hitung persentase aktifitas KD, SW, Denda, dan Total untuk periode saat ini dibandingkan periode yang sama tahun lalu
    if aktifitas_kd_last_year != 0:
        persentase_kd = (total_kd / aktifitas_kd_last_year - 1) * 100
    else:
        persentase_kd = 0

    if aktifitas_sw_last_year != 0:
        persentase_sw = (total_sw / aktifitas_sw_last_year - 1) * 100
    else:
        persentase_sw = 0

    if aktifitas_denda_last_year != 0:
        persentase_denda = (total_denda / aktifitas_denda_last_year - 1) * 100
    else:
        persentase_denda = 0

    if aktifitas_total_last_year != 0:
        persentase_total = (total / aktifitas_total_last_year - 1) * 100
    else:
        persentase_total = 0

    
    # Tampilkan tampilan total KD, SW, DENDA, dan chart performa setiap loket:
    st.markdown('### SEKTOR 34 SWDKLLJ PERIODE {} s.d. {}'.format(start_date.strftime('%d-%m-%Y'), end_date.strftime('%d-%m-%Y')))

    col1, col2, col3 = st.columns(3)
    col1.metric("Total KD", "Rp {:,.0f}".format(total_kd), "{:.2f}%".format(persentase_kd))
    col2.metric("Total SW", "Rp {:,.0f}".format(total_sw), "{:.2f}%".format(persentase_sw))
    col3.metric("Total Denda", "Rp {:,.0f}".format(total_denda), "{:.2f}%".format(persentase_denda))

    st.markdown("<div style='text-align: left; font-size: 36px;'>Total Rp {:,.0f}</div>".format(total), unsafe_allow_html=True)
    st.markdown("<div style='text-align: left; font-size: 20px;'>Aktivitas Total {:.2f}%</div>".format(persentase_total), unsafe_allow_html=True)

    


    # Tampilkan persentase realisasi KD, SW, Denda, dan Total
    st.markdown('### PERSENTASE REALISASI SWDKLLJ 2023')
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    
    # Create a pie chart for realisasi KD
    with col1:
        kd_data = [realisasi_kd, 100-realisasi_kd]
        kd_labels = ["Realisasi KD", "Belum Tercapai"]
        kd_colors = ["#3f69aa", "#dbdbdb"]

        kd_fig = go.Figure(data=[go.Pie(labels=kd_labels, values=kd_data, hole=0.5, marker_colors=kd_colors)])
        kd_fig.update_layout(title_text="Realisasi KD", width=400, margin=dict(l=10, r=10, b=5, t=30))


        # Show the KD figure
        st.plotly_chart(kd_fig)

    # Create a pie chart for realisasi KD
    with col2:
        sw_data = [realisasi_sw, 100-realisasi_sw]
        sw_labels = ["Realisasi SW", "Belum Tercapai"]
        sw_colors = ["#3f69aa", "#dbdbdb"]

        sw_fig = go.Figure(data=[go.Pie(labels=sw_labels, values=sw_data, hole=0.5, marker_colors=sw_colors)])
        sw_fig.update_layout(title_text="Realisasi SW", width=400, margin=dict(l=10, r=10, b=5, t=30))

        # Show the KD figure
        st.plotly_chart(sw_fig)

    # Create a pie chart for realisasi denda
    with col3:
        denda_data = [realisasi_denda, 100-realisasi_denda]
        denda_labels = ["Realisasi denda", "Belum Tercapai"]
        denda_colors = ["#3f69aa", "#dbdbdb"]

        denda_fig = go.Figure(data=[go.Pie(labels=denda_labels, values=denda_data, hole=0.5, marker_colors=denda_colors)])
        denda_fig.update_layout(title_text="Realisasi DENDA", width=400, margin=dict(l=10, r=10, b=5, t=30))

        # Show the KD figure
        st.plotly_chart(denda_fig)

    # Create a pie chart for realisasi total
    with col4:
        total_data = [realisasi_total, 100-realisasi_total]
        total_labels = ["Realisasi total", "Belum Tercapai"]
        total_colors = ["#3f69aa", "#dbdbdb"]

        total_fig = go.Figure(data=[go.Pie(labels=total_labels, values=total_data, hole=0.5, marker_colors=total_colors)])
        total_fig.update_layout(title_text="Realisasi TOTAL", width=400, margin=dict(l=10, r=10, b=5, t=30))

        # Show the KD figure
        st.plotly_chart(total_fig)

    # Read the data from the database table and create a DataFrame
    cursor.execute("SELECT * FROM tb_siklikal")
    data = cursor.fetchall()
    df_siklikal = pd.DataFrame(data, columns=["no", "TANGGAL", "siklikal", "normal"])

    # Filter the DataFrame based on the selected date range
    mask_siklikal = (df_siklikal['TANGGAL'] >= pd.to_datetime(start_date)) & (df_siklikal['TANGGAL'] <= pd.to_datetime(end_date))
    filtered_df_siklikal = df_siklikal.loc[mask_siklikal]

    # Calculate the total target "siklikal" and "normal" for the selected date range
    total_siklikal = filtered_df_siklikal['siklikal'].sum()
    total_normal = filtered_df_siklikal['normal'].sum()


    # Calculate the percentage of the total target "siklikal" and "normal" for the selected date range
    total = df_siklikal[['siklikal', 'normal']].sum().sum()
    perc_siklikal = total_siklikal * 100
    perc_normal = total_normal * 100

    siklikal_kd = (realisasi_kd - perc_siklikal)
    siklikal_sw = (realisasi_sw - perc_siklikal)
    siklikal_denda = (realisasi_denda - perc_siklikal)
    siklikal_total = (realisasi_total - perc_siklikal)
    normal_kd = (realisasi_kd - perc_normal)
    normal_sw = (realisasi_sw - perc_normal)
    normal_denda = (realisasi_denda - perc_normal)
    normal_total = (realisasi_total - perc_normal)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"Realisasi KD vs Siklikal sd {end_date.strftime('%B %Y')} ({perc_siklikal:.2f}%)", "{:.2f}%".format(realisasi_kd), "{:.2f}%".format(siklikal_kd))
    col1.metric(f"Realisasi KD vs Normal Avg sd {end_date.strftime('%B %Y')} ({perc_normal:.2f}%)", "{:.2f}%".format(realisasi_kd), "{:.2f}%".format(normal_kd))
    col2.metric(f"Realisasi SW vs Siklikal sd {end_date.strftime('%B %Y')} ({perc_siklikal:.2f}%)", "{:.2f}%".format(realisasi_sw), "{:.2f}%".format(siklikal_sw))
    col2.metric(f"Realisasi SW vs Normal Avg sd {end_date.strftime('%B %Y')} ({perc_normal:.2f}%)", "{:.2f}%".format(realisasi_sw), "{:.2f}%".format(normal_sw))
    col3.metric(f"Realisasi DENDA vs Siklikal sd {end_date.strftime('%B %Y')} ({perc_siklikal:.2f}%)", "{:.2f}%".format(realisasi_denda), "{:.2f}%".format(siklikal_denda))
    col3.metric(f"Realisasi DENDA vs Normal Avg sd {end_date.strftime('%B %Y')} ({perc_normal:.2f}%)", "{:.2f}%".format(realisasi_denda), "{:.2f}%".format(normal_denda))
    col4.metric(f"Realisasi TOTAL vs Siklikal sd {end_date.strftime('%B %Y')} ({perc_siklikal:.2f}%)", "{:.2f}%".format(realisasi_total), "{:.2f}%".format(siklikal_total))
    col4.metric(f"Realisasi TOTAL vs Normal Avg sd {end_date.strftime('%B %Y')} ({perc_normal:.2f}%)", "{:.2f}%".format(realisasi_total), "{:.2f}%".format(normal_total))
 

### Membuat 2 kolom
    col1, col2 = st.columns(2)

### Ini koding buat tabel aktifitas perloket %
    # Filter data for selected loket and current period
    with col1:
        mask = (df['TANGGAL'] >= pd.to_datetime(start_date)) & (df['TANGGAL'] <= pd.to_datetime(end_date)) & (df['LOKET'].isin(selected_loket))
        filtered_df = df.loc[mask]

        # Group data by loket and calculate the sum of each activity for the current period
        grouped_df = filtered_df.groupby(['LOKET']).sum()[['KD', 'SW', 'DENDA']]
        grouped_df['TOTAL'] = grouped_df.sum(axis=1)

        # Filter data for selected loket and same period last year
        start_date_last_year = start_date.replace(year=start_date.year - 1)
        end_date_last_year = end_date.replace(year=end_date.year - 1)
        mask_last_year = (df['TANGGAL'] >= pd.to_datetime(start_date_last_year)) & (df['TANGGAL'] <= pd.to_datetime(end_date_last_year)) & (df['LOKET'].isin(selected_loket))
        filtered_df_last_year = df.loc[mask_last_year]

        # Group data by loket and calculate the sum of each activity for the same period last year
        grouped_df_last_year = filtered_df_last_year.groupby(['LOKET']).sum()[['KD', 'SW', 'DENDA']]
        grouped_df_last_year['TOTAL'] = grouped_df_last_year.sum(axis=1)

        # Merge data for the current period and same period last year
        merged_df = grouped_df.merge(grouped_df_last_year, left_index=True, right_index=True, suffixes=('_current', '_last_year'))

        # Calculate the percentage of each activity for the current period compared to the same period last year
        merged_df['Aktifitas_kd'] = (merged_df['KD_current'] / merged_df['KD_last_year'] - 1) * 100
        merged_df['Aktifitas_sw'] = (merged_df['SW_current'] / merged_df['SW_last_year'] - 1) * 100
        merged_df['Aktifitas_denda'] = (merged_df['DENDA_current'] / merged_df['DENDA_last_year'] - 1) * 100
        merged_df['Aktifitas_total'] = (merged_df['TOTAL_current'] / merged_df['TOTAL_last_year'] - 1) * 100

        # Sort merged_df by persentase_total in descending order
        merged_df = merged_df.sort_values(by='Aktifitas_total', ascending=False)

        # Remove rows with NaN values
        merged_df.dropna(subset=['Aktifitas_kd', 'Aktifitas_sw', 'Aktifitas_denda', 'Aktifitas_total'], inplace=True)

        # Display the percentage of each activity per loket
        st.write("Aktifitas Per Loket (%)")
        st.write(merged_df[['Aktifitas_kd', 'Aktifitas_sw', 'Aktifitas_denda', 'Aktifitas_total']].applymap('{:.2f}%'.format))

### Membuat tabel aktifitas perloket
    with col2:
        # Filter data based on selected date range and loket
        mask = (df['TANGGAL'] >= pd.to_datetime(start_date)) & (df['TANGGAL'] <= pd.to_datetime(end_date)) & (df['LOKET'].isin(selected_loket))
        filtered_df = df.loc[mask]

        # Get total revenue for each loket
        grouped_df = filtered_df.groupby('LOKET').agg({'KD': 'sum', 'SW': 'sum', 'DENDA': 'sum'})

        # Merge with target data for each loket
        target_loket = target_df[target_df['LOKET'].isin(selected_loket)]
        grouped_df = pd.merge(grouped_df, target_loket, on='LOKET')

        # Calculate the percentage of achievement towards the annual target for each loket
        grouped_df['realisasi_kd'] = grouped_df['KD'] / grouped_df['TARGET_KD'] * 100
        grouped_df['realisasi_sw'] = grouped_df['SW'] / grouped_df['TARGET_SW'] * 100
        grouped_df['realisasi_denda'] = grouped_df['DENDA'] / grouped_df['TARGET_DENDA'] * 100
        grouped_df['realisasi_total'] = grouped_df[['KD', 'SW', 'DENDA']].sum(axis=1) / grouped_df[['TARGET_KD', 'TARGET_SW', 'TARGET_DENDA']].sum(axis=1) * 100

        # Remove rows with a value of 0
        grouped_df = grouped_df.loc[grouped_df[['KD', 'SW', 'DENDA']].any(axis=1)]

        # Sort the DataFrame by realisasi_total in descending order
        grouped_df = grouped_df.sort_values(by=['realisasi_total'], ascending=False)

        # Convert realisasi_total values to a percentage format
        grouped_df['realisasi_kd'] = grouped_df['realisasi_kd'].apply(lambda x: '{:.2f}%'.format(x))
        grouped_df['realisasi_sw'] = grouped_df['realisasi_sw'].apply(lambda x: '{:.2f}%'.format(x))
        grouped_df['realisasi_denda'] = grouped_df['realisasi_denda'].apply(lambda x: '{:.2f}%'.format(x))
        grouped_df['realisasi_total'] = grouped_df['realisasi_total'].apply(lambda x: '{:.2f}%'.format(x))

        # Display the table
        st.markdown('Realisasi Per Loket 2023 (%)')
        grouped_df = grouped_df.set_index('LOKET')
        st.dataframe(grouped_df[['realisasi_kd', 'realisasi_sw', 'realisasi_denda', 'realisasi_total']])


### Membuat 2 kolom
    col1, col2 = st.columns(2)


### Ini koding buat grafik timeseries
    # Mengembalikan Dataframe ke semula
    with col1:
        mask = (df['TANGGAL'] >= pd.to_datetime(start_date)) & (df['TANGGAL'] <= pd.to_datetime(end_date)) & (df['LOKET'].isin(selected_loket))
        filtered_df = df.loc[mask]

        # Hitung total KD, SW, DENDA:
        filtered_df['TOTAL'] = filtered_df['KD'] + filtered_df['SW'] + filtered_df['DENDA']
        total_kd = filtered_df['KD'].sum()
        total_sw = filtered_df['SW'].sum()
        total_denda = filtered_df['DENDA'].sum()
        total = total_kd + total_sw + total_denda

        # Tampilkan TANGGAL dan TOTAL tertinggi, terendah, dan rata-rata
        st.markdown('### Timeseries')
        highest_total = filtered_df['TOTAL'].max()
        highest_date = filtered_df.loc[filtered_df['TOTAL'] == highest_total, 'TANGGAL'].values[0]
        

        # Create a bar chart using Plotly Express
        fig = px.bar(filtered_df, x='TANGGAL', y='TOTAL')

        # Add dropdown filters to the chart
        fig.update_layout(
            updatemenus=[
                dict(
                    buttons=list([
                        dict(
                            args=[{'y': [filtered_df['TOTAL']]}, {'title': 'Total: Rp {:,.2f}'.format(total)}],
                            label='Total All',
                            method='update'
                        ),
                        dict(
                            args=[{'y': [filtered_df['KD']]}, {'title': 'Total KD: Rp {:,.2f}'.format(total_kd)}],
                            label='Total KD',
                            method='update'
                        ),
                        dict(
                            args=[{'y': [filtered_df['SW']]}, {'title': 'Total SW: Rp {:,.2f}'.format(total_sw)}],
                            label='Total SW',
                            method='update'
                        ),
                        dict(
                            args=[{'y': [filtered_df['DENDA']]}, {'title': 'Total Denda: Rp {:,.2f}'.format(total_denda)}],
                            label='Total Denda',
                            method='update'
                        )                  
                    ]),
                    direction='down',
                    showactive=True,
                    xanchor='left',
                    yanchor='top',
                    x=0.5,
                    y=1.15
                ),
            ]
        )
       


    # Display the highest and lowest TOTAL with their respective dates
        st.write(f"Total tertinggi terjadi pada tanggal:", highest_date, "dengan nilai: Rp {:,.2f}".format(highest_total))


        # Display the chart in Streamlit
        st.plotly_chart(fig)


### Ini koding membuat grafik timeseries perloket
    # Membuat Plot line chart
    with col2:
        st.markdown('### Performa LOKET Harian')
        chart_data = merged_df[['TOTAL_current']].reset_index().rename(columns={'TOTAL_current': 'TOTAL'}).sort_values('TOTAL', ascending=False)
        chart_data = filtered_df.groupby(['TANGGAL', 'LOKET'])[['KD', 'SW', 'DENDA', 'TOTAL']].sum().reset_index()

        # Filter LOKET tidak sama dengan 0
        chart_data = chart_data[chart_data['LOKET'] != 0]

        chart_data['TANGGAL'] = pd.to_datetime(chart_data['TANGGAL'])

        line_chart = alt.Chart(chart_data).mark_line(point=True, strokeWidth=2).encode(
            x=alt.X('TANGGAL', title='Tanggal'),
            y=alt.Y('TOTAL', title='Total Pendapatan'),
            color=alt.Color('LOKET', title='Loket'),
            tooltip=['TANGGAL', 'LOKET', 'KD', 'SW', 'DENDA', 'TOTAL']
        ).properties(
            width=900,
            height=500
        )

        st.altair_chart(line_chart)

# Fungsi untuk menampilkan halaman potensi (Page 2)
def potensi():
    # Load env variables
#     load_dotenv()

    # Koneksi ke database
    mydb = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USERNAME'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_DATABASE')
    )
    cursor = mydb.cursor()

    # Membaca file database tb_potensi
    cursor.execute("SELECT * FROM tb_potensi")
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["no", "kd_wil", "nm_kecamatan", "nm_kelurahan", "kode_plat", "jumlah", "loket_samsat", "latitude", "longitude"])

    
    
    st.sidebar.markdown(f"### Potensi Kendaraan Perwakilan Bogor")
    subtotal_jumlah = df["jumlah"].sum() 
    st.sidebar.markdown(f"Total Potensi: **{subtotal_jumlah:,}**")


    # Mengubah nilai pada kolom kode_plat menjadi nama plat
    df["nama_plat"] = df["kode_plat"].replace({
        1: "Plat Hitam",
        2: "Plat Merah",
        3: "Plat Kuning"
    })

    # Mengelompokkan data berdasarkan kd_wil, nm_kecamatan dan nama_plat
    grouped_data = df.groupby(["kd_wil", "nm_kecamatan", "nama_plat"], as_index=False).agg({"jumlah": "sum"})

        # Reset index dan mengganti nama kolom index menjadi "Kode Wilayah"
    grouped_data = grouped_data.reset_index(drop=True)
    grouped_data = grouped_data.rename(columns={"kd_wil": "Kode Wilayah"})

        # Membuat tabel pivot untuk menampilkan data plat sebagai kolom terpisah
    pivot_table = pd.pivot_table(grouped_data, values="jumlah", index=["Kode Wilayah", "nm_kecamatan"],
                                  columns=["nama_plat"], aggfunc=sum, fill_value=0).reset_index()

    # Mengganti nama kolom pada dataframe
    pivot_table.columns = ["Kode Wilayah", "Nama Kecamatan", "Plat Hitam", "Plat Merah", "Plat Kuning"]

    # Menambahkan kolom Jumlah Kendaraan
    pivot_table["Jumlah Kendaraan"] = pivot_table.sum(axis=1)

    # Mengurutkan data frame berdasarkan kolom Jumlah Kendaraan secara descending
    pivot_table = pivot_table.sort_values(by=["Jumlah Kendaraan"], ascending=False)

    # Menghitung total jumlah kendaraan, jumlah kendaraan plat hitam, plat merah, dan plat kuning
    total_jumlah = pivot_table["Jumlah Kendaraan"].sum()
    total_hitam = pivot_table["Plat Hitam"].sum()
    total_merah = pivot_table["Plat Merah"].sum()
    total_kuning = pivot_table["Plat Kuning"].sum()
    
    
    # Reset index dan mengganti nama kolom index menjadi "Kode Wilayah"
    grouped_data = grouped_data.reset_index(drop=True)
    grouped_data = grouped_data.rename(columns={"kd_wil": "Kode Wilayah"})

    # Membuat tabel pivot untuk menampilkan data plat sebagai kolom terpisah
    pivot_table = pd.pivot_table(grouped_data, values="jumlah", index=["Kode Wilayah", "nm_kecamatan"],
                                  columns=["nama_plat"], aggfunc=sum, fill_value=0).reset_index()

    # Mengganti nama kolom pada dataframe
    pivot_table.columns = ["Kode Wilayah", "Nama Kecamatan", "Plat Hitam", "Plat Merah", "Plat Kuning"]

    # Menambahkan kolom Jumlah Kendaraan
    pivot_table["Jumlah Kendaraan"] = pivot_table.sum(axis=1)

    
    # Mengurutkan data frame berdasarkan kolom Jumlah Kendaraan secara descending
    pivot_table = pivot_table.sort_values(by=["Jumlah Kendaraan"], ascending=False)
    # Mengonversi pivot_table ke dataframe tanpa nomor index
    pivot_df = pd.DataFrame(pivot_table.to_records(index=False))

    # Menampilkan judul aplikasi web
    st.title("Potensi Kendaraan Tiap Loket Samsat Wilayah JR Bogor")

    # Menampilkan deskripsi aplikasi web
    st.markdown("Aplikasi web ini menampilkan jumlah kendaraan di setiap wilayah dan kecamatan berdasarkan plat kendaraan.")

    # Menambahkan filter berdasarkan kd_wil dalam bentuk tab
    kd_wil_dict = {10200: "Samsat Kabupaten Bogor",
                10300: "Samsat Kota Bogor",
                20100: "Samsat Depok",
                20110: "Samsat Cinere"} # dictionary of kd_wil values and their names

    selected_kd_wil = st.sidebar.selectbox("Pilih Wilayah", list(kd_wil_dict.values()))

    selected_kd_wil_code = list(kd_wil_dict.keys())[list(kd_wil_dict.values()).index(selected_kd_wil)]

    ### Membuat 2 kolom
    col1, col2 = st.columns(2)

    with col1:
        # Menampilkan tabel berdasarkan filter kd_wil yang dipilih
        filtered_table = pivot_table[pivot_table["Kode Wilayah"] == selected_kd_wil_code]
        filtered_table.set_index("Kode Wilayah", inplace=True)
        st.write(filtered_table)

    with col2:
        # Menampilkan grafik batang
        fig, ax = plt.subplots()
        bars = ax.bar(filtered_table["Nama Kecamatan"], filtered_table["Jumlah Kendaraan"])

        # Memperkecil ukuran font pada sumbu x dan y
        plt.xticks(fontsize=6, rotation='vertical')
        plt.yticks(fontsize=6)

        # Menampilkan grafik
        st.pyplot(fig)

   

    # Menampilkan total jumlah kendaraan dan jumlah plat kendaraan pada sidebar
    st.sidebar.markdown(f"### Total Potensi Kendaraan {selected_kd_wil}")
    total_jumlah = filtered_table["Jumlah Kendaraan"].sum()
    total_hitam = filtered_table["Plat Hitam"].sum()
    total_merah = filtered_table["Plat Merah"].sum()
    total_kuning = filtered_table["Plat Kuning"].sum()
    st.sidebar.markdown(f"Jumlah Kendaraan: **{total_jumlah:,}**")
    st.sidebar.markdown(f"Plat Hitam: **{total_hitam:,}**")
    st.sidebar.markdown(f"Plat Merah: **{total_merah:,}**")
    st.sidebar.markdown(f"Plat Kuning: **{total_kuning:,}**")

    # membuat objek peta folium dengan koordinat Bogor Jawa Barat sebagai titik tengah peta
    map = folium.Map(location=[-6.59680, 106.7899], zoom_start=100)

    map

# Konversi latitude dan longitude ke float
    df['latitude'] = df['latitude'] * 1e-6
    df['longitude'] = df['longitude'] * 1e-6

     # Inisialisasi peta dengan tampilan awal wilayah Bogor, Jawa Barat
    m = folium.Map(location=[-6.5937, 106.7890], zoom_start=12)

     # group data by kecamatan
    grouped_data = df.groupby('nm_kecamatan')

    # add markers for each group
    for kecamatan, group in grouped_data:
        kecamatan_location = (group['latitude'].mean(), group['longitude'].mean())
        total_jumlah = group['jumlah'].sum()
        popup_html = f"<b>{kecamatan}</b><br>Total Kendaraan: {total_jumlah}"
        folium.Marker(location=kecamatan_location, popup=popup_html).add_to(m)

    # Display map with Streamlit
    st.title("Jumlah Kendaraan Per Wilayah di Perwakilan Bogor")
    folium_static(m)

# Fungsi untuk menampilkan halaman upload (Page 3)
def upload():
    # Load nilai .env
#     load_dotenv()
    db_name =DB_DATABASE
    db_user =DB_USERNAME
    db_password =DB_PASSWORD
    db_host =DB_HOST
    db_port =DB_PORT

    st.title('Upload Data Monitoring')

    # Pilihan LOKET
    loket_dict = {
        "CABANG": "0300001",
        "CIREBON": "0300101",
        "TASIKMALAYA": "0300201",
        "SUKABUMI": "0300301",
        "PURWAKARTA": "0300401",
        "KARAWANG": "0300501",
        "BOGOR": "0300601",
        "BEKASI": "0300701",
        "BANDUNG": "0300801",
        "INDRAMAYU": "0300901"
    }
    default_loket = "BOGOR"
    loket = st.selectbox("Pilih Loket", list(loket_dict.keys()), index=list(loket_dict.keys()).index(default_loket))
    loket_code = loket_dict[loket]

    # Tanggal
    date = st.date_input("Tanggal")

    # Jika tombol "Ambil Data Monitoring" ditekan, maka buka URL dengan format yang sudah diubah
    if st.button("Ambil Data Monitoring"):
        # Mengubah format tanggal menjadi DD-MM-YYYY
        date_str = date.strftime("%d-%m-%Y")

        # URL dengan format tanggal dan kode loket yang sudah diubah
        url = f"https://ceri.jasaraharja.co.id/monitoring/swdkllj/datatables/{date_str}_{date_str}_{loket_code}_1"

        # Membuka URL
        st.write("Membuka URL: ", url)
        st.experimental_set_query_params(url=urllib.parse.quote_plus(url))
        webbrowser.open(url)

    # Membuat tombol untuk upload file JSON
    uploaded_file = st.file_uploader("Upload file JSON", type=["json"])

    # Jika file JSON sudah diupload, maka tampilkan isinya dalam bentuk tabel
    if uploaded_file is not None:
        # Membaca file JSON dan memuatnya ke dalam objek dictionary
        data = json.load(uploaded_file)

        # Memuat nilai dari kunci "data" ke dalam DataFrame pandas
        df = pd.DataFrame(data["data"], columns=["kantor_jr", "jml_kd", "jml_sw", "jml_denda", "total"])
        df = df.rename(columns={"kantor_jr": "LOKET", 
                        "jml_kd": "KD", 
                        "jml_sw": "SW", 
                        "jml_denda": "DENDA", 
                        "total": "TOTAL"})

        # Mengambil tanggal dari nama file
        tanggal_str = uploaded_file.name.split("_")[0]
        # Mengubah format tanggal dari string ke objek datetime.date
        tanggal = datetime.datetime.strptime(tanggal_str, "%d-%m-%Y").date()

        # Menambahkan kolom tanggal ke dalam dataframe
        df.insert(0, "TANGGAL", tanggal)

        # Menampilkan DataFrame dalam bentuk tabel
        st.write(df)

        # Menambahkan tombol untuk mengupload data ke database
        if st.button("Upload to Database"):
            try:
                # Terhubung ke database
                cnx = mysql.connector.connect(
                    user=db_user, password=db_password, host=db_host, database=db_name, ssl_disabled=True
                )

                # Buat cursor untuk melakukan operasi database
                cursor = cnx.cursor()

                # Menyiapkan perintah SQL untuk memasukkan data ke dalam database
                add_data = ("INSERT INTO tb_pendapatan34"
                            "(TANGGAL, LOKET, KD, SW, DENDA, TOTAL) "
                            "VALUES (%(tanggal)s, %(loket)s, %(kd)s, %(sw)s, %(denda)s, %(total)s)")

                # Memasukkan data ke dalam database
                # Memasukkan data ke dalam database
                for i, row in df.iterrows():
                    data = {
                        'tanggal': row['TANGGAL'],
                        'loket': row['LOKET'],
                        'kd': row['KD'],
                        'sw': row['SW'],
                        'denda': row['DENDA'],
                        'total': row['TOTAL']
                    }
                    
                    # Periksa apakah data dengan TANGGAL dan LOKET yang sama sudah ada di dalam database
                    check_data = ("SELECT COUNT(*) FROM tb_pendapatan34 "
                                "WHERE TANGGAL = %(tanggal)s AND LOKET = %(loket)s")
                    cursor.execute(check_data, data)
                    result = cursor.fetchone()

                    if result[0] == 0:
                        # Jika data belum ada, maka masukkan data ke dalam database
                        cursor.execute(add_data, data)
                    else:
                        # Jika data sudah ada, maka lewati data ini dan lanjut ke data berikutnya
                        continue

                # Commit perubahan pada database
                cnx.commit()

                # Menampilkan notifikasi bila data berhasil dimasukkan ke dalam database
                st.success("Data berhasil diupload ke dalam database!")
            except Error as e:
                st.error(f"Terjadi kesalahan: {e}")

# Fungsi untuk menampilkan halaman blast (Page 4)
def blast():
    # Load env variables
#     load_dotenv()

    # Set locale ke bahasa Indonesia dan format uang Rupiah
#     locale.setlocale(locale.LC_ALL, 'id_ID')

    # Koneksi ke database
#     mydb = mysql.connector.connect(
#     host=os.getenv('DB_HOST'),
#     user=os.getenv('DB_USERNAME'),
#     password=os.getenv('DB_PASSWORD'),
#     database=os.getenv('DB_DATABASE')
#     )
#     cursor = mydb.cursor()


    st.title('Whatsapp Blast')

    # Membaca data dari tabel pendapatan_sw di database
    cursor.execute("SELECT * FROM tb_pendapatan34")
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["NO", "TANGGAL", "LOKET", "KD", "SW", "DENDA", "TOTAL"])


    # Membaca data dari tabel target di database
    cursor.execute("SELECT * FROM tb_target")
    data = cursor.fetchall()
    target_df = pd.DataFrame(data, columns=["NO", "LOKET", "TARGET_KD", "TARGET_SW", "TARGET_DENDA", "TARGET_IW"])


    # Tampilkan tanggal terakhir data diperbaharui
    last_update = df['TANGGAL'].max().strftime('%d %B %Y')
    st.write(f"Data terakhir yang akan dikirimkan adalah pendapatan sampai dengan {last_update}")

    # Load data dari tabel pendapatan_sw di database dan ubah tipe data kolom TANGGAL menjadi datetime
    cursor.execute("SELECT * FROM tb_pendapatan34")
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["NO", "TANGGAL", "LOKET", "KD", "SW", "DENDA", "TOTAL"])
    df['TANGGAL'] = pd.to_datetime(df['TANGGAL'])

    # Buat sidebar dengan widget untuk memilih rentang tanggal dan filter LOKET:
    start_date = st.sidebar.date_input("Start date", datetime.date(2023, 1, 1), min_value=df['TANGGAL'].min().date(), max_value=df['TANGGAL'].max().date())
    end_date = st.sidebar.date_input("End date", df['TANGGAL'].max().date(), min_value=start_date, max_value=df['TANGGAL'].max().date())


    loket_list = df['LOKET'].unique().tolist()
    loket_list.append('PERWAKILAN BOGOR')

    mask = (df['TANGGAL'] >= pd.to_datetime(start_date)) & (df['TANGGAL'] <= pd.to_datetime(end_date)) & (df['LOKET'].isin(loket_list))
    filtered_df = df.loc[mask]

    # Group data by loket and calculate the sum of each activity for the current period
    grouped_df = filtered_df.groupby(['LOKET']).sum()[['KD', 'SW', 'DENDA']]
    grouped_df['TOTAL'] = grouped_df.sum(axis=1)

    # Hilangkan baris dengan total nol
    grouped_df = grouped_df.loc[grouped_df['TOTAL'] != 0]

    # Membuat baris baru Perwakilan Bogor Total Semua Loket
    grouped_df.loc['PERWAKILAN BOGOR'] = grouped_df.sum()

    # Filter data for selected loket and same period last year
    start_date_last_year = start_date.replace(year=start_date.year - 1)
    end_date_last_year = end_date.replace(year=end_date.year - 1)
    mask_last_year = (df['TANGGAL'] >= pd.to_datetime(start_date_last_year)) & (df['TANGGAL'] <= pd.to_datetime(end_date_last_year)) & (df['LOKET'].isin(loket_list))
    filtered_df_last_year = df.loc[mask_last_year]

    # Group data by loket and calculate the sum of each activity for the same period last year
    grouped_df_last_year = filtered_df_last_year.groupby(['LOKET']).sum()[['KD', 'SW', 'DENDA']]
    grouped_df_last_year['TOTAL'] = grouped_df_last_year.sum(axis=1)

    # Membuat baris baru Perwakilan Bogor Total Semua Loket
    grouped_df_last_year.loc['PERWAKILAN BOGOR'] = grouped_df_last_year.sum()

    # Merge data for the current period and same period last year
    merged_df = grouped_df.merge(grouped_df_last_year, left_index=True, right_index=True, suffixes=('_current', '_last_year'))

    # Calculate the percentage of each activity for the current period compared to the same period last year
    merged_df['Aktifitas_kd'] = (merged_df['KD_current'] / merged_df['KD_last_year'] - 1) * 100
    merged_df['Aktifitas_sw'] = (merged_df['SW_current'] / merged_df['SW_last_year'] - 1) * 100
    merged_df['Aktifitas_denda'] = (merged_df['DENDA_current'] / merged_df['DENDA_last_year'] - 1) * 100
    merged_df['Aktifitas_total'] = (merged_df['TOTAL_current'] / merged_df['TOTAL_last_year'] - 1) * 100

    # Mencari aktifitas total perwakilan
    merged_df.loc['PERWAKILAN BOGOR', 'Aktifitas_kd'] = (merged_df.loc['PERWAKILAN BOGOR', 'KD_current'] / merged_df.loc['PERWAKILAN BOGOR', 'KD_last_year'] - 1) * 100
    merged_df.loc['PERWAKILAN BOGOR', 'Aktifitas_sw'] = (merged_df.loc['PERWAKILAN BOGOR', 'SW_current'] / merged_df.loc['PERWAKILAN BOGOR', 'SW_last_year'] - 1) * 100
    merged_df.loc['PERWAKILAN BOGOR', 'Aktifitas_denda'] = (merged_df.loc['PERWAKILAN BOGOR', 'DENDA_current'] / merged_df.loc['PERWAKILAN BOGOR', 'DENDA_last_year'] - 1) * 100
    merged_df.loc['PERWAKILAN BOGOR', 'Aktifitas_total'] = (merged_df.loc['PERWAKILAN BOGOR', 'TOTAL_current'] / merged_df.loc['PERWAKILAN BOGOR', 'TOTAL_last_year'] - 1) * 100
    

    # Get total revenue for each loket
    grouped_df_target = filtered_df.groupby(['LOKET']).sum()[['KD', 'SW', 'DENDA']]
    # Membuat baris baru Perwakilan Bogor Total Semua Loket
    grouped_df_target.loc['PERWAKILAN BOGOR'] = grouped_df_target.sum()

    # Merge with target data for each loket
    target_loket = target_df[target_df['LOKET'].isin(loket_list)]
    grouped_df_target = pd.merge(grouped_df_target, target_loket, on='LOKET')

    # Calculate the percentage of achievement towards the annual target for each loket
    grouped_df_target['realisasi_kd'] = grouped_df_target['KD'] / grouped_df_target['TARGET_KD'] * 100
    grouped_df_target['realisasi_sw'] = grouped_df_target['SW'] / grouped_df_target['TARGET_SW'] * 100
    grouped_df_target['realisasi_denda'] = grouped_df_target['DENDA'] / grouped_df_target['TARGET_DENDA'] * 100
    grouped_df_target['realisasi_total'] = grouped_df_target[['KD', 'SW', 'DENDA']].sum(axis=1) / grouped_df_target[['TARGET_KD', 'TARGET_SW', 'TARGET_DENDA']].sum(axis=1) * 100
    
    # Convert realisasi_total values to a percentage format
    grouped_df_target['realisasi_kd'] = grouped_df_target['realisasi_kd'].apply(lambda x: '{:.2f}%'.format(x))
    grouped_df_target['realisasi_sw'] = grouped_df_target['realisasi_sw'].apply(lambda x: '{:.2f}%'.format(x))
    grouped_df_target['realisasi_denda'] = grouped_df_target['realisasi_denda'].apply(lambda x: '{:.2f}%'.format(x))
    grouped_df_target['realisasi_total'] = grouped_df_target['realisasi_total'].apply(lambda x: '{:.2f}%'.format(x))
    grouped_df_target = grouped_df_target.set_index('LOKET')

        # Read the data from the database table and create a DataFrame
    cursor.execute("SELECT * FROM tb_siklikal")
    data = cursor.fetchall()
    df_siklikal = pd.DataFrame(data, columns=["no", "TANGGAL", "siklikal", "normal"])

    # Filter the DataFrame based on the selected date range
    mask_siklikal = (df_siklikal['TANGGAL'] >= pd.to_datetime(start_date)) & (df_siklikal['TANGGAL'] <= pd.to_datetime(end_date))
    filtered_df_siklikal = df_siklikal.loc[mask_siklikal]

    # Calculate the total target "siklikal" and "normal" for the selected date range
    total_siklikal = filtered_df_siklikal['siklikal'].sum()
    total_normal = filtered_df_siklikal['normal'].sum()


    # Calculate the percentage of the total target "siklikal" and "normal" for the selected date range
    total = df_siklikal[['siklikal', 'normal']].sum().sum()
    perc_siklikal = total_siklikal * 100
    perc_normal = total_normal * 100


    # Display the percentage of each activity per loket
    st.write("Data yang akan dikirimkan tiap loket")
    
    combined_df = grouped_df.join(merged_df[['KD_last_year', 'SW_last_year', 'DENDA_last_year', 'TOTAL_last_year', 'Aktifitas_kd', 'Aktifitas_sw', 'Aktifitas_denda', 'Aktifitas_total']])
    combined_df = combined_df.join(grouped_df_target[['realisasi_kd', 'realisasi_sw', 'realisasi_denda', 'realisasi_total']])
    
    # Create new columns for perc_siklikal and perc_normal with same values for all rows
    combined_df['perc_siklikal'] = pd.Series([perc_siklikal] * len(combined_df), index=combined_df.index)
    combined_df['perc_normal'] = pd.Series([perc_normal] * len(combined_df), index=combined_df.index)


    # Format percentage columns
    combined_df[['Aktifitas_kd', 'Aktifitas_sw', 'Aktifitas_denda', 'Aktifitas_total', 'perc_siklikal', 'perc_normal']] = combined_df[['Aktifitas_kd', 'Aktifitas_sw', 'Aktifitas_denda', 'Aktifitas_total', 'perc_siklikal', 'perc_normal']].applymap('{:.2f}%'.format)
    

    # membuat dictionary dengan data nomor telepon
    telepon = {
             'SAMSAT KOTA BOGOR': '+6285921258252',
             'SAMSAT KAB. BOGOR': '+628118492525',
             'SAMSAT DEPOK': '+6285266253431',
             'SAMSAT CINERE': '+6281251127411',
             'SAMSAT ITC DEPOK': '+6281370901737',
             'SAMSAT ITC CIBINONG': '+6282125308099',
             'SAMSAT ONLINE BSD': '+6281251127411',
             'SAMSAT OUTLET BTM': '+6282282843355',
             'SAMSAT OUTLET CILEUNGSI': '+6282118974111',
             'SAMSAT OUTLET SAWANGAN': '+6281219014064',
             'SAMSAT OUTLET LEUWILIANG': '+6285782677446',
             'SAMSAT KELILING KOTA BOGOR': '+6285921258252',
             'SAMSAT KELILING KAB. BOGOR': '+6285719712875',
             'SAMSAT KELILING DEPOK': '+6285266253431',
             'SAMSAT KELILING CINERE': '+6281251127411',
             'SAMSAT MPP KOTA BOGOR': '+628999997007',
             'SAMSAT OUTLET MALL BOXIES 123': '+6281809209005',
             'PERWAKILAN BOGOR': '+6281222566778'}
    

    # membuat DataFrame dari dictionary
    telepon_df = pd.DataFrame.from_dict(telepon, orient='index', columns=['TELEPON'])

    # menggabungkan dataFrame telepon_df dengan combined_df dengan kolom 'LOKET'
    combined_df = combined_df.merge(telepon_df, left_on='LOKET', right_index=True)

    # Display combined_df
    st.write(combined_df)

    # mengubah format tanggal enddate
    end_date = end_date.strftime('%B %Y')
    

    # Menambahkan kolom "SEND" pada data frame
    combined_df['SEND Whatsapp Blast ANEV'] = ''

    # Menambahkan tombol "SEND" pada tampilan Streamlit
#     if st.button('SEND Whatsapp Blast ANEV'):
#         for loket, row in combined_df.iterrows():
            
#             message = f'Hai *{loket}* ini adalah SIPjarbor\nBerikut adalah Hasil pendapatan {loket} sampai dengan tanggal {last_update}\n\nKD : {"Rp {:,.0f}".format(row["KD"])} dan Tahun Lalu {"Rp {:,.0f}".format(row["KD_last_year"])}\nSW : {"Rp {:,.0f}".format(row["SW"])}  dan Tahun Lalu {"Rp {:,.0f}".format(row["SW_last_year"])}\nDENDA : {"Rp {:,.0f}".format(row["DENDA"])}  dan Tahun Lalu {"Rp {:,.0f}".format(row["DENDA_last_year"])}\nTOTAL : {"Rp {:,.0f}".format(row["TOTAL"])}  dan Tahun Lalu {"Rp {:,.0f}".format(row["TOTAL_last_year"])}\n\nAktifitas_kd : {row["Aktifitas_kd"]}\nAktifitas_sw : {row["Aktifitas_sw"]}\nAktifitas_denda : {row["Aktifitas_denda"]}\nAktifitas_total : {row["Aktifitas_total"]}\n\nrealisasi_kd : {row["realisasi_kd"]}\nrealisasi_sw : {row["realisasi_sw"]}\nrealisasi_denda : {row["realisasi_denda"]}\nrealisasi_total : {row["realisasi_total"]}\nTarget bulanan Siklikal & Nasional sd {end_date} adalah {row["perc_siklikal"]} dan {row["perc_normal"]}\nTetap Semangat. JR BOGOR PASTI BISA..\n*URAAAAAAAA*'
#             kit.sendwhatmsg(row['TELEPON'], message, datetime.datetime.now().hour, datetime.datetime.now().minute +2)
#             combined_df.at[loket, 'SEND'] = 'Sent'
#         st.success('Whatsapp Blast Samsat successfully!')



#         # tampilan aplikasi
#     st.title('Broadcast WhatsApp')
#     st.write('Masukkan pesan, pilih nomor telepon, serta lampiran dokumen atau gambar.')

#     pesan = st.text_area('Pesan (max 200 karakter)', max_chars=200)

#     # menampilkan pilihan nomor telepon dalam bentuk checkbox
#     nomor_telepon = st.multiselect('Pilih nomor telepon', options=list(telepon.keys()))


#     # mengirimkan pesan dan lampiran ketika tombol "Kirim Pesan" ditekan
#     if st.button('Kirim Pesan'):
#         for nomor in nomor_telepon:
#             kit.sendwhatmsg(telepon[nomor], pesan, datetime.datetime.now().hour, datetime.datetime.now().minute +1)  # kirim pesan
            
#         # Menampilkan pesan bahwa pesan teks telah berhasil dikirim
#         st.write(f'Pesan teks berhasil dikirim ke nomor {nomor}')

# Fungsi untuk logout
def logout():
    session_state.logged_in = False
    session_state.user_type = ""
    st.success("Logout berhasil!")

# Membuat Session State
session_state = st.session_state
if not hasattr(session_state, "logged_in"):
    session_state.logged_in = False
if not hasattr(session_state, "user_type"):
    session_state.user_type = ""

# Menambahkan halaman-halaman ke aplikasi
st.set_page_config(page_title="SIPJARBOR" , layout='wide', initial_sidebar_state='expanded')

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


if not session_state.logged_in:
    st.title("Login")
    login()
else:
    st.title("Sistem Informasi Pendapatan Jasa Raharja Bogor")
    menu = ["Home", "Potensi"]
    if session_state.user_type == "admin":
        menu += ["Upload", "Blast"]
    menu += ["Logout"]
    choice = st.sidebar.selectbox("Select a page", menu)

    if choice == "Home":
        home()
    elif choice == "Potensi":
        potensi()
    elif choice == "Upload" and session_state.user_type == "admin":
        upload()
    elif choice == "Blast" and session_state.user_type == "admin":
        blast()
    elif choice == "Logout":
        logout()
    else:
        st.warning("Anda tidak memiliki hak akses untuk halaman ini.")
