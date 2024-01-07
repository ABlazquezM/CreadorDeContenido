from tkinter import *
from tkinter import ttk
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import tkinter as tk
import re
from unidecode import unidecode 
import webbrowser

def abrir_ventana_guardar():
    
    def guardar(tabla, url, informacion):
        with sqlite3.connect('datosScraping.db') as conexion:
            cursor = conexion.cursor()
        
            # Verificar si ya existe el registro antes de la inserción
            cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE url = ? AND informacion = ?", (url, informacion))
            registroExistente = cursor.fetchone()[0]

            if not registroExistente:
                # Evitar posibles problemas de SQL injection utilizando parámetros de la consulta
                cursor.execute(f"INSERT INTO {tabla} (url, informacion) VALUES (?, ?)", (url, informacion))
                #contenidoInfo.set(f"Guardado en {tabla}: {url}, {informacion}")
                info.insert("1.0", f"Guardado en {tabla}: {url}, {informacion}\n")
                conexion.commit()
            else:
                #contenidoInfo.set(f"Registro existente en {tabla}: {url}, {informacion}")
                info.insert("1.0", f"Registro existente en {tabla}: {url}, {informacion}\n")
                
        conexion.close()

    #CREAMOS UN ARCHIVO PARA GUARDAR LA URL:
    def listaUrls(urlNueva):
        # Verificamos si la URL ya existe en el archivo

        try:
            # Verificamos si el archivo existe
            archivo = open("urls.txt", 'r')
            urlsExistentes = archivo.read().splitlines()
            archivo.close()
        except FileNotFoundError:
            # Si el archivo no existe, lo creamos
            archivo = open("urls.txt", 'w')
            urlsExistentes = []
            archivo.close()


        if urlNueva not in urlsExistentes:
            # Si la URL no existe, añadir al final del archivo
            
            archivo = open("urls.txt", 'a')
            archivo.write(f"{urlNueva}\n")
            info.delete("1.0", "end")
            info.insert("1.0", f"URL añadida: {urlNueva}\n")
            archivo.close()
            return True
                
        else:
            info.delete("1.0", "end")
            info.insert("1.0", f"La URL ya existe en el archivo: {urlNueva}\n")
            return False


    def raspado(urls, etiquetas):
        for url in urls: #Verificamos si hay alguna url inválida
            parsed_url = urlparse(url)
            if not (parsed_url.scheme and parsed_url.netloc):
                print(f"URL inválida: {url}")
                continue
            if listaUrls(url):
                contenido = requests.get(url)
                sopa = BeautifulSoup(contenido.text, 'html.parser')

                for etiqueta in etiquetas:
                    elementos = sopa.find_all(etiqueta)
                    
                    for elemento in elementos:
                        if etiqueta == 'a':
                            # Si la etiqueta es 'a' (enlace), obtener la URL del atributo 'href'
                            informacion = elemento.get('href')
                            if informacion is not None and not informacion.startswith(('https:', '//',"http:")):
                                continue
                        elif etiqueta == 'img':
                            # Si la etiqueta es 'img' (imagen), obtener la URL del atributo 'src'
                            informacion = elemento.get('src')
                            # Agregar condición para verificar si la URL comienza con 'https' o '//'
                            if informacion is not None and not informacion.startswith(('https:', '//',"http:")):
                                continue  # Salta a la siguiente iteración si no cumple con la condición
                        else:
                            # En otros casos, obtener el texto del elemento
                            informacion = elemento.text.strip()

                        # Guardar en la base de datos
                        guardar(etiqueta, url, informacion)

    def guardarURL(): 
        nuevaURL = url.get()
        listaUrl.append(nuevaURL)
        info.delete("1.0", "end")
        raspado(listaUrl, listaEtiquetas)
        url.set("")



    ventanaGuardar = tk.Toplevel()

    ventanaGuardar.config(bd=15)
    ventanaGuardar.title("Guardar")
    ventanaGuardar.resizable(1, 1)
    ventanaGuardar.iconbitmap("perro.ico")

    cont = ttk.Frame(ventanaGuardar, padding=10)
    cont.grid()

    #VARIABLES
    
    url = StringVar()
    listaEtiquetas = ["h1","p","a","img",]
    listaUrl =  []
   
        

    #Fila 1
    ttk.Label(cont, text="Nueva URL", font=("Helvetica", 8, "bold")).grid(row=0,padx=4, column=0,pady=5)         
    Entry(cont, width=100, justify="left",textvariable=url).grid(row=1, column=0,pady=5)
    Button(cont,text="CONFIRMAR",font=("Helvetica", 10, "bold"), bd=5, bg="#ffe6e6",width=10,command=guardarURL).grid(row=2,column=0,columnspan=2,pady=10)
    
    # Añadimos otro entry para indicar que cosas se están guardando 
    info = Text(cont, wrap="none", width=100, height=4, state="normal")
    info.grid(row=3, column=0, pady=5)
    info.insert("1.0","")

    #Añadimos un scroll para poder ver toda la info
    scrollbar = Scrollbar(cont, command=info.yview, orient="vertical")
    scrollbar.grid(row=3, column=1, sticky="ns")
    info.config(yscrollcommand=scrollbar.set)
    ventanaGuardar.mainloop()


def abrir_ventana_crear():
    def obtenerCincoConMasCoincidencias(lista, palabra):
        # Definir una expresión regular para buscar la palabra clave ignorando mayúsculas y minusculas
        patron = re.compile(re.escape(palabra), flags=re.IGNORECASE)

        # Creamos otra función para contar las veces que aparece las palabra clave en una cadena (ignorando mayúsculas y minusculas)
        def veces(cadena):
            return len(re.findall(patron, cadena.lower()))

        #Ordenamos los str por la cantidad de veces que se repite palabra
        listaOrdenada = sorted(lista, key=lambda x: veces(x), reverse=True)

        # Tomar las tres cadenas con más ocurrencias
        top5 = listaOrdenada[:5]
        return top5
    
    def generarContenido(palabra):
        #Vamos a guardar la palabra sin tildes para buscar las imágenes y los enlaces
        palabraSinTilde = unidecode(palabra)
        # Establecemos conexión con la BBDD
        with sqlite3.connect('datosScraping.db') as conexion:
            cursor = conexion.cursor()


            # Buscamos información en la BBDD
            # Buscamos un título
            cursor.execute("SELECT * FROM h1 WHERE informacion LIKE ?",
                        ('%' + palabra + '%',))

            h1 = cursor.fetchall()


            # Buscar los parrafos
            cursor.execute("SELECT * FROM p WHERE informacion LIKE ?",('%' + palabra + '%',))

            p = cursor.fetchall()
        
            # Escoger el mejor contenido
            parrafos = []
            for row in p:
                parrafo = row[2]
                parrafos.append(parrafo)


            # Busca imágenes, vamos a quitar los espacios para que salgan las palabras

            variantes = [palabraSinTilde.replace(' ', ''), palabraSinTilde.replace(
                ' ', '-'), palabraSinTilde.replace(' ', '_')]
            img = None
            for variante in variantes:
                cursor.execute(
                    "SELECT * FROM img WHERE informacion LIKE ?", ('%' + variante + '%',))
                img = cursor.fetchall()
                if img:
                    # Si se encuentramos datos, salimos del bucle
                    break   
            # Hacemos otro con las img:
            imagenes = []
            for row in img:
                imagen = row[2]

                if not imagen.startswith(("http:", "https:")):

                    # Si no comienza con "http: o https:" lo agregamos

                    imagen = "https:" + imagen

                imagenes.append(imagen)

            # Buscamos ENLACES relacionados
            variantes = [palabraSinTilde.replace(' ', ''), palabraSinTilde.replace(
                ' ', '-'), palabraSinTilde.replace(' ', '_')]
            a = None
            for variante in variantes:
                cursor.execute(
                    "SELECT * FROM a WHERE informacion LIKE ?", ('%' + variante + '%',))
                a = cursor.fetchall()
                if a:
                    # Si se encuentramos datos, salimos del bucle
                    break
            enlaces = []
            for row in a:
                enlace = row[2]
                if not enlace.startswith(("/w", "/wiki")):
                    if not enlace.startswith(("http:", "https:")):
                        # Si no comienza con "http: o https:" lo agregamos
                        enlace = "https:" + enlace

                    enlaces.append(enlace)


        top5Parrafo = obtenerCincoConMasCoincidencias(parrafos, palabra)

        top5Imagen = obtenerCincoConMasCoincidencias(imagenes, palabraSinTilde)


        # Generar un archivo HTML con el contenido obtenido

        with open('plantilla.html', 'r', encoding='utf-8') as template_file:

            template = template_file.read()


            # titulo

            template = template.replace(
                '<!--Título-->', f'{h1[0][2]}' if h1 else palabra)

            # enlace
            template = template.replace(
                'Enlace a la web', f'{h1[0][1]}' if h1 else '')

            # parrafo
            template = template.replace(
                '<!--Texto_Principal-->', f'{top5Parrafo[0]}' if top5Parrafo else '')


            # Enlace al párrafo ###########Pendiente de mejorar
            template = template.replace(
                '+info', f'{p[0][1]}' if top5Parrafo else '')

            # Imagen de logo
            template = template.replace(
                'Imagen logo', f'{top5Imagen[0]}' if top5Imagen else 'noImage.jpg')

            # imagen principal
            template = template.replace('Imagen principal', f'{top5Imagen[1]}' if top5Imagen and len(top5Imagen) > 1 else 'noImage.jpg')
            # Texto carrusel
            template = template.replace(
                '<!--Texto_carrusel-->', f'{top5Parrafo[1]}' if top5Parrafo else '')

            # Imagenes carrusel
            template = template.replace(
                'Imagen1', f'{top5Imagen[2]}' if top5Imagen and len(top5Imagen) > 2 else 'noImage.jpg')
            template = template.replace(
                'Imagen2', f'{top5Imagen[3]}' if top5Imagen and len(top5Imagen) > 3 else 'noImage.jpg')

            template = template.replace(
                'Imagen3', f'{top5Imagen[4]}' if top5Imagen and len(top5Imagen) > 4 else 'noImage.jpg')


            # Lista de enlaces relacionados
            template = template.replace('listaUno', f'{enlaces[0]}' if enlaces and len(enlaces) > 0 else '')
            template = template.replace('listaDos', f'{enlaces[1]}' if len(enlaces) > 1 else '')
            template = template.replace('listaTres', f'{enlaces[2]}' if len(enlaces) > 2 else '')
            template = template.replace('listaCuatro', f'{enlaces[3]}' if len(enlaces) > 3 else '')

        with open(f'{palabra}.html', 'w', encoding='utf-8') as output_file:

            output_file.write(template)

        webbrowser.open(f'{palabra}.html')
        

    def crearWeb(): 
        nuevaRaza = raza.get()
        generarContenido(nuevaRaza)
        raza.set("")
    

    ventanaCrear = tk.Toplevel()

    ventanaCrear.config(bd=15)
    ventanaCrear.title("Crear")
    ventanaCrear.resizable(1, 1)
    ventanaCrear.iconbitmap("perro.ico")

    cont = ttk.Frame(ventanaCrear, padding=10)
    cont.grid()

    raza = StringVar()

    ttk.Label(cont, text="¿Sobre que raza quiere crear la web?", font=("Helvetica", 8, "bold")).grid(row=0,padx=4, column=0,pady=5)         
    Entry(cont, width=40, justify="left",textvariable=raza).grid(row=1, column=0,pady=5)
    Button(cont,text="CREAR",font=("Helvetica", 10, "bold"), bd=5, bg="#ffe6e6",width=10,command=crearWeb).grid(row=2,column=0,columnspan=2,pady=10)
    


principal = Tk()
principal.config(bd=15) 
principal.title("Principal")
principal.resizable(0,0)

principal.iconbitmap("perro.ico")

contenedor = ttk.Frame(principal,padding=10).grid()



ttk.Label(contenedor, text="Generador de contenido perruno", font=("Helvetica", 15, "bold")).grid(row=0, column=0, padx=5, pady=5, columnspan=2, sticky='n')
Label(contenedor,text="").grid(row=6,column=0)


img = PhotoImage(file="perro.png").subsample(4)

Label(contenedor,image=img).grid(row=2,column=0,columnspan=2, pady=25)

#Botones
Button(contenedor, text="Guardar URL", font=("Helvetica", 12, "bold"), bd=5, bg="#ffe6e6",width=15,command=abrir_ventana_guardar).grid(row=3, column=0, padx=10, pady=5)
Button(contenedor,text="Generar contenido", font=("Helvetica", 12, "bold"), bd=5, bg="#ffe6e6",width=15,command=abrir_ventana_crear).grid(row=3,column=1, padx=20, pady=5) 



principal.mainloop()



