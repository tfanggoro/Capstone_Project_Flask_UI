from flask import Flask, render_template
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
playstore = pd.read_csv('data/googleplaystore.csv')
playstore.drop_duplicates(subset = 'App', keep='first')

# bagian ini untuk menghapus row 10472 karena nilai data tersebut tidak tersimpan pada kolom yang benar
playstore.drop([10472], inplace=True)

# bagian ini untuk mengubah tipe data kolom 'Category','Content Rating','Genres','Type' menjadi 'category'
categorical=['Category','Content Rating','Genres','Type']
playstore[categorical] = playstore[categorical].astype('category')

# bagian ini untuk menghilangkan karakter ',' dan '+' pada kolom installs
playstore.Installs = playstore['Installs'].apply(lambda x: x.replace(',',''))
playstore.Installs = playstore['Installs'].apply(lambda x: x.replace('+',''))

# Bagian ini untuk merapikan kolom Size, Anda tidak perlu mengubah apapun di bagian ini
playstore['Size'].replace('Varies with device', np.nan, inplace = True ) 
playstore.Size = (playstore.Size.replace(r'[kM]+$', '', regex=True).astype(float) * \
             playstore.Size.str.extract(r'[\d\.]+([kM]+)', expand=False)
            .fillna(1)
            .replace(['k','M'], [10**3, 10**6]).astype(int))
playstore['Size'].fillna(playstore.groupby('Category')['Size'].transform('mean'),inplace = True)

# bagian ini untuk menghilangkan karakter '$' dan merubah tipe data kolom 'Price' menjadi float64
playstore.Price = playstore['Price'].apply(lambda x: x.replace('$',''))
playstore.Price = playstore['Price'].astype('float64')

# bagian ini untuk merubah tipe data Reviews, Size, Installs ke dalam tipe data integer
dtype_integer=['Reviews','Size','Installs']
playstore[dtype_integer]=playstore[dtype_integer].astype('int64')

@app.route("/")
# This fuction for rendering the table
def index():
    df2 = playstore.copy()

    # Membuat tabel frequency pada kolom 'Category'
    top_category = pd.crosstab( index=df2['Category'],
                                columns='Jumlah',
                                values=df2['Category'],
                                aggfunc='count'
                              ).sort_values(by='Jumlah', ascending=False).reset_index()
    # Dictionary stats digunakan untuk menyimpan beberapa data yang digunakan untuk menampilkan nilai di value box dan tabel
    stats = {
        'most_categories' : top_category.iloc[0,0],
        'total': top_category.iloc[0,1],
        'rev_table' : playstore.groupby(by=['Category','App'])\
                                .agg({'Reviews':'sum','Rating':'mean'})\
                                .sort_values(by='Reviews', ascending=False)\
                                .reset_index().head(10)\
                                .to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
    }

    ## Bar Plot
    cat_order = df2.groupby('Category').agg({
    'Category' : 'count'
        }).rename({'Category':'Total'}, axis=1).sort_values(by='Total',ascending=False).head(5).reset_index()
    X = cat_order['Category']
    Y = cat_order['Total']  
    my_colors = ['r','g','b','k','y','m','c']
    # bagian ini digunakan untuk membuat kanvas/figure
    fig = plt.figure(figsize=(8,3),dpi=300)
    fig.add_subplot()
    # bagian ini digunakan untuk membuat bar plot
    plt.barh(X,Y, color=my_colors)
    # bagian ini digunakan untuk menyimpan plot dalam format image.png
    plt.savefig('01.cat_order.png',bbox_inches="tight")

    # bagian ini digunakan untuk mengconvert matplotlib png ke base64 agar dapat ditampilkan ke template html
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    # variabel result akan dimasukkan ke dalam parameter di fungsi render_template() agar dapat ditampilkan di 
    # halaman html
    result = str(figdata_png)[2:-1]
    
    ## Scatter Plot
    X = df2['Reviews'].values # axis x
    Y = df2['Rating'].values # axis y
    area = playstore['Installs'].values/10000000 # ukuran besar/kecilnya lingkaran scatter plot
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    # isi nama method untuk scatter plot, variabel x, dan variabel y
    plt.scatter(x=X,y=Y, s=area, alpha=0.3)
    plt.xlabel('Reviews')
    plt.ylabel('Rating')
    plt.savefig('02. rev_rat.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result2 = str(figdata_png)[2:-1]

    ## Histogram Size Distribution
    X=(df2['Size']/1000000).values
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.hist(X,bins=100, density=True,  alpha=0.75)
    plt.xlabel('Size')
    plt.ylabel('Frequency')
    plt.savefig('03. hist_size.png',bbox_inches="tight")
    
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result3 = str(figdata_png)[2:-1]

    ## Buatlah sebuah plot yang menampilkan insight di dalam data 
    cat_playstore = playstore[(playstore['Rating']>4.5)].dropna()
    pd.crosstab(index=cat_playstore['Category'],
                columns='Total Number of Apps',
                ).sort_values(by='Total Number of Apps', ascending=False)\
                 .head(10)\
                 .plot(kind='bar')
    plt.savefig('04. bar_categorynum.png',bbox_inches="tight")
    
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result4 = str(figdata_png)[2:-1]

    # Tambahkan hasil result plot pada fungsi render_template()
    return render_template('index.html', stats=stats, result=result, result2=result2, result3=result3, result4=result4)

if __name__ == "__main__": 
    app.run(debug=True)
