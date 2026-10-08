import flet as ft
import requests
import os

# Compatibilidad para versiones recientes de Flet (Colors e Icons)
if not hasattr(ft, "Colors"):
    ft.Colors = ft.colors
if not hasattr(ft, "Icons"):
    ft.Icons = ft.icons
    
BASE_URL = "https://inventario-cdps-backend.onrender.com/api"

BACKEND_URL = f"{BASE_URL}/productos/"
VENTAS_URL = f"{BASE_URL}/ventas/"
VENTAS_HOY_URL = f"{BASE_URL}/ventas/hoy/"
CIERRE_URL = f"{BASE_URL}/cierre/"
TASA_URL = f"{BASE_URL}/config/tasa/"
ESTADISTICAS_URL = f"{BASE_URL}/estadisticas/"
CARGA_URL = f"{BASE_URL}/stock/cargar/"
DESCARGA_URL = f"{BASE_URL}/stock/descargar/"
KARDEX_URL = f"{BASE_URL}/kardex/"
ALERTAS_URL = f"{BASE_URL}/productos/alertas/"
DEVOLUCION_URL = f"{BASE_URL}/devoluciones/"
LOGIN_URL = f"{BASE_URL}/login"
EXCEL_SUBIR_URL = f"{BASE_URL}/productos/cargar-excel/"
EXCEL_REPORT_URL = f"{BASE_URL}/reportes/excel/"
PDF_CIERRE_URL = f"{BASE_URL}/reportes/cierre-pdf/"

def main(page: ft.Page):
    page.title = "Inventario CDPS - SaaS Multi-Dispositivo"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#090D16"
    page.padding = 10

    session = {"token": "", "username": "", "nombre": "", "rol": ""}
    tasa_bcv = [36.00]
    carrito_items = []
    modo_edicion = {"activo": False, "sku": ""}

    # --- LISTAS UI ---
    lista_productos = ft.ListView(expand=True, spacing=10)
    lista_kardex_ui = ft.ListView(expand=True, spacing=5)
    lista_alertas_ui = ft.ListView(expand=True, spacing=5)
    lista_ventas_hoy_ui = ft.ListView(expand=True, spacing=5)
    lista_top_productos_ui = ft.ListView(expand=True, spacing=5)
    lista_cierres_ui = ft.ListView(expand=True, spacing=5)

    # --- COMPONENTES CAJA & ARQUEO ---
    tasa_in = ft.TextField(label="Tasa BCV (Bs/$)", value="36.00", width=130, keyboard_type=ft.KeyboardType.NUMBER, border_color="#374151")
    lbl_total_dia_usd = ft.Text("Total Hoy: $0.00 USD", size=16, weight=ft.FontWeight.BOLD, color="#34D399")
    lbl_total_dia_bs = ft.Text("Total Hoy: Bs. 0.00", size=14, color="#9CA3AF")
    
    lbl_efectivo_usd = ft.Text("Efectivo ($): $0.00", size=12, color=ft.Colors.WHITE)
    lbl_efectivo_bs = ft.Text("Efectivo (Bs): $0.00", size=12, color=ft.Colors.WHITE)
    lbl_pago_movil = ft.Text("Pago Móvil/Transf: $0.00", size=12, color=ft.Colors.WHITE)
    lbl_tarjeta = ft.Text("Tarjeta: $0.00", size=12, color=ft.Colors.WHITE)

    arq_efectivo_usd_in = ft.TextField(label="Conteo Billetes ($)", value="0.00", keyboard_type=ft.KeyboardType.NUMBER, border_color="#374151")
    arq_efectivo_bs_in = ft.TextField(label="Conteo Efectivo (Bs)", value="0.00", keyboard_type=ft.KeyboardType.NUMBER, border_color="#374151")
    arq_obs_in = ft.TextField(label="Observaciones del Cierre", value="", border_color="#374151")

    # --- COMPONENTES POS ---
    sku_venta_in = ft.TextField(label="SKU del Producto", border_color="#374151", focused_border_color="#10b981", expand=True)
    cant_venta_in = ft.TextField(label="Cant", value="1", width=80, keyboard_type=ft.KeyboardType.NUMBER, border_color="#374151", focused_border_color="#10b981")
    lista_carrito_ui = ft.ListView(expand=True, spacing=5)
    lbl_total_pagar = ft.Text("Total: $0.00 USD", size=18, weight=ft.FontWeight.BOLD, color="#34D399")
    
    recibido_usd_in = ft.TextField(label="Recibido en USD ($)", value="", keyboard_type=ft.KeyboardType.NUMBER, border_color="#374151")
    recibido_bs_in = ft.TextField(label="Recibido en Bs (Digital)", value="", keyboard_type=ft.KeyboardType.NUMBER, border_color="#374151")
    lbl_vuelto_calc = ft.Text("Esperando pago...", size=14, weight=ft.FontWeight.BOLD, color="#9CA3AF")

    metodo_pago_dropdown = ft.Dropdown(
        label="Método de Pago",
        value="Efectivo ($)",
        options=[
            ft.dropdown.Option("Efectivo ($)"),
            ft.dropdown.Option("Efectivo (Bs)"),
            ft.dropdown.Option("Pago Móvil / Transferencia"),
            ft.dropdown.Option("Tarjeta Débito/Crédito"),
            ft.dropdown.Option("Pago Mixto"),
        ],
        border_color="#374151"
    )
    cliente_in = ft.TextField(label="Nombre del Cliente", value="Cliente General", border_color="#374151")

    # --- ALMACÉN & DEVOLUCIONES ---
    sku_almacen_in = ft.TextField(label="SKU del Producto", border_color="#374151")
    cant_almacen_in = ft.TextField(label="Cantidad", value="1", keyboard_type=ft.KeyboardType.NUMBER, border_color="#374151")
    motivo_almacen_in = ft.TextField(label="Motivo / Detalle", value="Ajuste de inventario", border_color="#374151")

    sku_dev_in = ft.TextField(label="SKU Producto Devuelto", border_color="#374151")
    cant_dev_in = ft.TextField(label="Cantidad", value="1", keyboard_type=ft.KeyboardType.NUMBER, border_color="#374151")
    motivo_dev_in = ft.TextField(label="Motivo (Ej. Defecto de fábrica)", value="Devolución de cliente", border_color="#374151")
    metodo_dev_dropdown = ft.Dropdown(
        label="Método de Reembolso",
        value="Efectivo ($)",
        options=[
            ft.dropdown.Option("Efectivo ($)"),
            ft.dropdown.Option("Efectivo (Bs)"),
            ft.dropdown.Option("Pago Móvil / Transferencia"),
            ft.dropdown.Option("Tarjeta Débito/Crédito"),
        ],
        border_color="#374151"
    )

    lbl_facturado_global = ft.Text("Total Acumulado: $0.00 USD", size=16, weight=ft.FontWeight.BOLD, color="#34D399")

    # --- BANNERS & NOTIFICACIONES ---
    banner_alerta = ft.Banner(
        bgcolor="#1f2937",
        leading=ft.Icon(ft.Icons.WARNING, color=ft.Colors.AMBER, size=30),
        content=ft.Text("", color=ft.Colors.WHITE),
        actions=[ft.TextButton("Cerrar", on_click=lambda e: cerrar_banner())]
    )
    page.overlay.append(banner_alerta)

    def cerrar_banner():
        banner_alerta.open = False
        page.update()

    def mostrar_mensaje(texto, es_error=False):
        banner_alerta.content.value = texto
        banner_alerta.leading.color = ft.Colors.RED if es_error else ft.Colors.GREEN
        banner_alerta.open = True
        page.update()

    def set_dialog_open(dialog, is_open):
        dialog.open = is_open
        page.update()

    # --- EXCEL FILE PICKER ---
    def procesar_archivo_excel_seleccionado(e: ft.FilePickerResultEvent):
        if not e.files: return
        file_path = e.files[0].path
        try:
            with open(file_path, "rb") as f:
                files = {"file": (e.files[0].name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                resp = requests.post(EXCEL_SUBIR_URL, files=files)
                if resp.status_code == 200:
                    mostrar_mensaje(f"¡Éxito! {resp.json()['mensaje']}")
                    cargar_inventario()
                else:
                    mostrar_mensaje(resp.json().get("detail", "Error en Excel."), True)
        except Exception as ex:
            mostrar_mensaje(f"Error al subir: {ex}", True)

    file_picker_excel = ft.FilePicker(on_result=procesar_archivo_excel_seleccionado)
    page.overlay.append(file_picker_excel)

    def descargar_reporte_excel(e):
        try:
            resp = requests.get(EXCEL_REPORT_URL)
            if resp.status_code == 200:
                with open("Reporte_Inventario_CDPS.xlsx", "wb") as f: f.write(resp.content)
                mostrar_mensaje("¡Excel guardado como 'Reporte_Inventario_CDPS.xlsx'!")
            else: mostrar_mensaje("Error al generar Excel.", True)
        except Exception as ex: mostrar_mensaje(f"Error de descarga: {ex}", True)

    def descargar_pdf_cierre(e):
        try:
            resp = requests.get(PDF_CIERRE_URL)
            if resp.status_code == 200:
                with open("Ticket_Cierre_CDPS.pdf", "wb") as f: f.write(resp.content)
                mostrar_mensaje("¡PDF guardado como 'Ticket_Cierre_CDPS.pdf'!")
            else: mostrar_mensaje("Error al generar PDF.", True)
        except Exception as ex: mostrar_mensaje(f"Error de descarga: {ex}", True)

    # --- CALCULADORA DE VUELTO ---
    def calcular_vuelto_dinamico(e=None):
        total_global = sum(item['subtotal'] for item in carrito_items)
        if total_global == 0:
            lbl_vuelto_calc.value = "Esperando pago..."
            lbl_vuelto_calc.color = "#9CA3AF"
            page.update()
            return

        try: usd_in = float(recibido_usd_in.value) if recibido_usd_in.value.strip() else 0.0
        except ValueError: usd_in = 0.0

        try: bs_in = float(recibido_bs_in.value) if recibido_bs_in.value.strip() else 0.0
        except ValueError: bs_in = 0.0

        total_ingresado_usd = usd_in + (bs_in / tasa_bcv[0])
        diferencia = total_ingresado_usd - total_global

        if diferencia > 0.001:
            lbl_vuelto_calc.value = f"Vuelto: ${diferencia:.2f} USD (Bs. {diferencia * tasa_bcv[0]:,.2f})"
            lbl_vuelto_calc.color = "#10b981"
        elif diferencia < -0.001:
            falta = abs(diferencia)
            lbl_vuelto_calc.value = f"Falta: ${falta:.2f} USD (Bs. {falta * tasa_bcv[0]:,.2f})"
            lbl_vuelto_calc.color = "#EF4444"
        else:
            lbl_vuelto_calc.value = "¡Pago Exacto! ✔️"
            lbl_vuelto_calc.color = "#3B82F6"

        page.update()

    recibido_usd_in.on_change = calcular_vuelto_dinamico
    recibido_bs_in.on_change = calcular_vuelto_dinamico

    # --- DATOS API ---
    def cargar_tasa_bcv():
        try:
            resp = requests.get(TASA_URL)
            if resp.status_code == 200:
                val = resp.json().get("tasa", 36.00)
                tasa_bcv[0] = val
                tasa_in.value = str(val)
        except Exception: pass
        page.update()

    def actualizar_tasa(e):
        try:
            nueva_tasa = float(tasa_in.value)
            resp = requests.post(TASA_URL, json={"tasa": nueva_tasa})
            if resp.status_code == 200:
                tasa_bcv[0] = nueva_tasa
                mostrar_mensaje("¡Tasa BCV actualizada exitosamente!")
                cargar_ventas_hoy()
                actualizar_totales_carrito()
            else: mostrar_mensaje("Error al actualizar tasa.", True)
        except Exception: mostrar_mensaje("Ingrese una tasa válida.", True)

    def cargar_inventario():
        lista_productos.controls.clear()
        try:
            respuesta = requests.get(BACKEND_URL)
            if respuesta.status_code == 200:
                productos = respuesta.json()
                if not productos:
                    lista_productos.controls.append(ft.Text("No hay productos registrados.", color="#9CA3AF", text_align=ft.TextAlign.CENTER))
                for prod in productos:
                    color_stock = "#10b981" if prod['stock'] > prod['stock_minimo'] else "#EF4444"
                    tarjeta = ft.Container(
                        bgcolor="#1f2937",
                        border_radius=10,
                        padding=12,
                        content=ft.Column([
                            ft.Row([
                                ft.Text(prod['nombre'], weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.WHITE),
                                ft.Text(f"${prod['precio']:.2f}", color="#34D399", size=15, weight=ft.FontWeight.BOLD),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([
                                ft.Text(f"SKU: {prod['sku']} | Color: {prod.get('color', 'N/A')}", color="#9CA3AF", size=12),
                                ft.Text(f"Stock: {prod['stock']}", color=color_stock, size=13, weight=ft.FontWeight.BOLD)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(color="#374151", height=10),
                            ft.Row([
                                ft.TextButton("✏️ Editar", on_click=lambda e, p=prod: abrir_modal_edicion(p)),
                                ft.TextButton("🗑️ Eliminar", style=ft.ButtonStyle(color=ft.Colors.RED_400), on_click=lambda e, s=prod['sku']: confirmar_eliminacion(s))
                            ], alignment=ft.MainAxisAlignment.END)
                        ])
                    )
                    lista_productos.controls.append(tarjeta)
        except Exception: pass
        page.update()

    # --- FORMULARIO PRODUCTO & MODAL ---
    sku_in = ft.TextField(label="SKU / Código", border_color="#374151")
    nombre_in = ft.TextField(label="Nombre del Producto", border_color="#374151")
    cat_in = ft.TextField(label="Categoría", border_color="#374151")
    color_in = ft.TextField(label="Color", value="N/A", border_color="#374151")
    costo_in = ft.TextField(label="Costo Unitario ($)", keyboard_type=ft.KeyboardType.NUMBER, border_color="#374151")
    precio_in = ft.TextField(label="Precio Venta ($)", keyboard_type=ft.KeyboardType.NUMBER, border_color="#374151")
    stock_in = ft.TextField(label="Stock Inicial", value="10", keyboard_type=ft.KeyboardType.NUMBER, border_color="#374151")
    min_in = ft.TextField(label="Stock Mínimo", value="5", keyboard_type=ft.KeyboardType.NUMBER, border_color="#374151")
    prov_in = ft.TextField(label="Proveedor", border_color="#374151")

    def guardar_nuevo_producto(e):
        try:
            payload = {
                "sku": sku_in.value.strip(),
                "nombre": nombre_in.value.strip(),
                "categoria": cat_in.value.strip(),
                "color": color_in.value.strip() or "N/A",
                "costo": float(costo_in.value),
                "precio": float(precio_in.value),
                "stock": int(stock_in.value),
                "stock_minimo": int(min_in.value),
                "proveedor": prov_in.value.strip()
            }
            resp = requests.put(f"{BACKEND_URL}{modo_edicion['sku']}/", json=payload) if modo_edicion["activo"] else requests.post(BACKEND_URL, json=payload)
            if resp.status_code == 200:
                dlg_modal.open = False
                mostrar_mensaje("¡Producto guardado!")
                limpiar_formulario_producto()
                cargar_inventario()
            else: mostrar_mensaje(resp.json().get("detail", "Error al guardar."), True)
        except Exception: mostrar_mensaje("Verifique los valores numéricos.", True)

    def limpiar_formulario_producto():
        modo_edicion["activo"] = False
        modo_edicion["sku"] = ""
        sku_in.disabled = False
        for f in [sku_in, nombre_in, cat_in, costo_in, precio_in, prov_in]: f.value = ""
        color_in.value, stock_in.value, min_in.value = "N/A", "10", "5"

    def abrir_modal_edicion(prod):
        modo_edicion["activo"] = True
        modo_edicion["sku"] = prod['sku']
        sku_in.value, sku_in.disabled = prod['sku'], True
        nombre_in.value, cat_in.value, color_in.value = prod['nombre'], prod['categoria'], prod.get('color', 'N/A')
        costo_in.value, precio_in.value = str(prod['costo']), str(prod['precio'])
        stock_in.value, min_in.value, prov_in.value = str(prod['stock']), str(prod['stock_minimo']), prod['proveedor']
        dlg_modal.title.value = "✏️ Editar Producto"
        page.dialog = dlg_modal
        dlg_modal.open = True
        page.update()

    def confirmar_eliminacion(sku):
        def ejecutar_borrado(e):
            try:
                resp = requests.delete(f"{BACKEND_URL}{sku}/")
                if resp.status_code == 200:
                    dlg_confirm.open = False
                    mostrar_mensaje(f"Producto '{sku}' eliminado.")
                    cargar_inventario()
                else: mostrar_mensaje("Error al eliminar.", True)
            except Exception as ex: mostrar_mensaje(f"Error de conexión: {ex}", True)

        dlg_confirm = ft.AlertDialog(
            title=ft.Text("⚠️ Confirmar Eliminación"),
            content=ft.Text(f"¿Eliminar el SKU '{sku}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: set_dialog_open(dlg_confirm, False)),
                ft.ElevatedButton("Eliminar", bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE, on_click=ejecutar_borrado)
            ]
        )
        page.dialog = dlg_confirm
        dlg_confirm.open = True
        page.update()

    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("✨ Registrar Producto", color="#10b981", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column([sku_in, nombre_in, cat_in, color_in, costo_in, precio_in, stock_in, min_in, prov_in], scroll=ft.ScrollMode.AUTO, height=350),
            width=380
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: cerrar_modal()),
            ft.ElevatedButton("Guardar", bgcolor="#059669", color=ft.Colors.WHITE, on_click=guardar_nuevo_producto)
        ]
    )

    def cerrar_modal():
        dlg_modal.open = False
        limpiar_formulario_producto()
        page.update()

    def abrir_modal_nuevo(e):
        limpiar_formulario_producto()
        dlg_modal.title.value = "✨ Registrar Producto"
        page.dialog = dlg_modal
        dlg_modal.open = True
        page.update()

    # --- DEVOLUCIONES ---
    def ejecutar_devolucion_pos(e):
        try:
            payload = {
                "sku": sku_dev_in.value.strip(),
                "cantidad": int(cant_dev_in.value),
                "metodo_reembolso": metodo_dev_dropdown.value,
                "motivo": motivo_dev_in.value.strip() or "Devolución"
            }
            resp = requests.post(DEVOLUCION_URL, json=payload)
            if resp.status_code == 200:
                res = resp.json()
                dlg_devolucion.open = False
                mostrar_mensaje(f"Reembolso: ${res['total_reembolsado_usd']:.2f} USD")
                sku_dev_in.value, cant_dev_in.value = "", "1"
                cargar_inventario()
                cargar_ventas_hoy()
                cargar_kardex()
            else: mostrar_mensaje(resp.json().get("detail", "Error en devolución."), True)
        except Exception: mostrar_mensaje("Verifique los datos.", True)

    dlg_devolucion = ft.AlertDialog(
        modal=True,
        title=ft.Text("🔄 Procesar Devolución", color="#EF4444", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column([sku_dev_in, cant_dev_in, metodo_dev_dropdown, motivo_dev_in], scroll=ft.ScrollMode.AUTO, height=280),
            width=380
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: set_dialog_open(dlg_devolucion, False)),
            ft.ElevatedButton("💵 Reembolsar", bgcolor="#DC2626", color=ft.Colors.WHITE, on_click=ejecutar_devolucion_pos)
        ]
    )

    def abrir_modal_devolucion(e):
        page.dialog = dlg_devolucion
        dlg_devolucion.open = True
        page.update()

    # --- VENTAS Y CAJA ---
    def cargar_ventas_hoy():
        lista_ventas_hoy_ui.controls.clear()
        try:
            resp = requests.get(VENTAS_HOY_URL)
            if resp.status_code == 200:
                data = resp.json()
                lbl_total_dia_usd.value = f"Total Hoy: ${data['total_general_usd']:.2f} USD"
                lbl_total_dia_bs.value = f"Total Hoy: Bs. {data['total_general_bs']:,.2f}"
                
                totales = data['totales']
                lbl_efectivo_usd.value = f"Efectivo ($): ${totales.get('Efectivo ($)', 0.0):.2f}"
                lbl_efectivo_bs.value = f"Efectivo (Bs): ${totales.get('Efectivo (Bs)', 0.0):.2f}"
                lbl_pago_movil.value = f"Pago Móvil/Transf: ${totales.get('Pago Móvil / Transferencia', 0.0):.2f}"
                lbl_tarjeta.value = f"Tarjeta / Mixto: ${totales.get('Tarjeta Débito/Crédito', 0.0) + totales.get('Pago Mixto', 0.0):.2f}"

                for v in data['ventas']:
                    lista_ventas_hoy_ui.controls.append(
                        ft.Container(
                            bgcolor="#1f2937", padding=8, border_radius=6,
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(f"{v['nombre']} (x{v['cantidad']})", color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Cliente: {v['cliente']} | Pago: {v['metodo_pago']}", color="#9CA3AF", size=11)
                                ], expand=True),
                                ft.Text(f"${v['total_venta']:.2f}", color="#34D399", size=12, weight=ft.FontWeight.BOLD)
                            ])
                        )
                    )
        except Exception: pass
        page.update()

    def procesar_cierre_caja(e):
        try:
            payload = {
                "efectivo_usd_fisc": float(arq_efectivo_usd_in.value or 0.0),
                "efectivo_bs_fisc": float(arq_efectivo_bs_in.value or 0.0),
                "observaciones": arq_obs_in.value.strip() or "Cierre sin novedad"
            }
            resp = requests.post(CIERRE_URL, json=payload)
            if resp.status_code == 200:
                res = resp.json()
                dif = res['diferencia_usd']
                msg = f"Diferencia: ${dif:.2f} USD" if dif != 0 else "¡Caja cuadrada!"
                mostrar_mensaje(f"¡Cierre registrado! {msg}")
                arq_efectivo_usd_in.value, arq_efectivo_bs_in.value, arq_obs_in.value = "0.00", "0.00", ""
                cargar_ventas_hoy()
                cargar_estadisticas()
            else: mostrar_mensaje("Error al cerrar.", True)
        except Exception: mostrar_mensaje("Verifique los valores de arqueo.", True)

    def cargar_estadisticas():
        lista_top_productos_ui.controls.clear()
        lista_cierres_ui.controls.clear()
        try:
            resp = requests.get(ESTADISTICAS_URL)
            if resp.status_code == 200:
                data = resp.json()
                lbl_facturado_global.value = f"Facturación Acumulada: ${data['total_facturado_usd']:.2f} USD ({data['total_transacciones']} ventas)"
                for item in data['top_productos']:
                    lista_top_productos_ui.controls.append(
                        ft.Container(
                            bgcolor="#1f2937", padding=8, border_radius=6,
                            content=ft.Row([
                                ft.Text(f"🥇 {item['nombre']}", color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
                                ft.Text(f"Vendidos: {item['total_vendido']} u. | ${item['total_ingreso']:.2f}", color="#34D399", size=12)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        )
                    )
                for c in data['historial_cierres']:
                    col_dif = "#10b981" if c['diferencia_usd'] >= 0 else "#EF4444"
                    lista_cierres_ui.controls.append(
                        ft.Container(
                            bgcolor="#1f2937", padding=8, border_radius=6,
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(f"Fecha: {c['fecha']}", color=ft.Colors.WHITE, size=11, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Obs: {c['observaciones']}", color="#9CA3AF", size=10)
                                ], expand=True),
                                ft.Column([
                                    ft.Text(f"Total: ${c['total_usd']:.2f}", color="#34D399", size=11, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Dif: ${c['diferencia_usd']:.2f}", color=col_dif, size=10)
                                ])
                            ])
                        )
                    )
        except Exception: pass
        page.update()

    def actualizar_totales_carrito():
        total = sum(item['subtotal'] for item in carrito_items)
        lbl_total_pagar.value = f"Total: ${total:.2f} USD (Bs. {total * tasa_bcv[0]:,.2f})"
        calcular_vuelto_dinamico()
        page.update()

    def agregar_al_carrito(e):
        sku = sku_venta_in.value.strip()
        try:
            cantidad = int(cant_venta_in.value)
            if cantidad <= 0: raise ValueError
        except ValueError:
            mostrar_mensaje("Cantidad inválida.", True)
            return

        if not sku:
            mostrar_mensaje("Ingrese SKU.", True)
            return

        try:
            resp = requests.get(BACKEND_URL)
            productos = resp.json()
            prod_encontrado = next((p for p in productos if p['sku'] == sku), None)
            
            if not prod_encontrado:
                mostrar_mensaje(f"SKU '{sku}' no encontrado.", True)
                return

            if prod_encontrado['stock'] < cantidad:
                mostrar_mensaje(f"Stock insuficiente. Disponible: {prod_encontrado['stock']}", True)
                return

            subtotal = cantidad * prod_encontrado['precio']
            carrito_items.append({
                "sku": sku,
                "nombre": prod_encontrado['nombre'],
                "precio": prod_encontrado['precio'],
                "cantidad": cantidad,
                "subtotal": subtotal
            })

            lista_carrito_ui.controls.clear()
            for item in carrito_items:
                lista_carrito_ui.controls.append(
                    ft.Container(
                        bgcolor="#1f2937", padding=10, border_radius=6,
                        content=ft.Row([
                            ft.Text(f"{item['nombre']} (x{item['cantidad']})", color=ft.Colors.WHITE, size=13),
                            ft.Text(f"${item['subtotal']:.2f}", color="#34D399", weight=ft.FontWeight.BOLD)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
                )
            sku_venta_in.value, cant_venta_in.value = "", "1"
            actualizar_totales_carrito()
        except Exception as ex: mostrar_mensaje(f"Error al agregar: {ex}", True)

    def procesar_venta_pos(e):
        if not carrito_items:
            mostrar_mensaje("Carrito vacío.", True)
            return

        total_factura_general = sum(item['subtotal'] for item in carrito_items)
        metodo = metodo_pago_dropdown.value

        try:
            usd_in = float(recibido_usd_in.value) if recibido_usd_in.value.strip() else 0.0
            bs_in = float(recibido_bs_in.value) if recibido_bs_in.value.strip() else 0.0
        except ValueError: usd_in, bs_in = 0.0, 0.0

        mix_usd_prop, mix_banco_prop = 0.0, 0.0

        if metodo == "Pago Mixto":
            total_ingresado = usd_in + (bs_in / tasa_bcv[0])
            if total_ingresado < total_factura_general:
                mostrar_mensaje(f"Monto insuficiente. Falta: ${total_factura_general - total_ingresado:.2f} USD", True)
                return
            if total_ingresado > 0:
                factor = total_factura_general / total_ingresado
                mix_usd_prop = usd_in * factor
                mix_banco_prop = (bs_in / tasa_bcv[0]) * factor

        try:
            for item in carrito_items:
                proporcion = (item['subtotal'] / total_factura_general) if total_factura_general > 0 else 0
                payload = {
                    "sku": item['sku'],
                    "cantidad": item['cantidad'],
                    "total_venta": item['subtotal'],
                    "metodo_pago": metodo,
                    "cliente": cliente_in.value.strip() or "Cliente General",
                    "mix_usd": mix_usd_prop * proporcion if metodo == "Pago Mixto" else 0.0,
                    "mix_banco": mix_banco_prop * proporcion if metodo == "Pago Mixto" else 0.0
                }
                resp = requests.post(VENTAS_URL, json=payload)
                if resp.status_code != 200:
                    mostrar_mensaje(resp.json().get("detail", "Error en transacción."), True)
                    return

            mostrar_mensaje("¡Venta procesada con éxito!")
            carrito_items.clear()
            lista_carrito_ui.controls.clear()
            recibido_usd_in.value, recibido_bs_in.value = "", ""
            actualizar_totales_carrito()
            cargar_inventario()
            cargar_ventas_hoy()
        except Exception as ex: mostrar_mensaje(f"Error de conexión: {ex}", True)

    def ejecutar_movimiento_stock(url_endpoint, tipo_accion):
        sku = sku_almacen_in.value.strip()
        try:
            cantidad = int(cant_almacen_in.value)
            if cantidad <= 0: raise ValueError
        except ValueError:
            mostrar_mensaje("Cantidad inválida.", True)
            return

        if not sku:
            mostrar_mensaje("Debe ingresar SKU.", True)
            return

        payload = {"sku": sku, "cantidad": cantidad, "motivo": motivo_almacen_in.value.strip() or f"{tipo_accion} manual"}

        try:
            resp = requests.post(url_endpoint, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                mostrar_mensaje(f"¡{tipo_accion} exitosa! Nuevo stock: {data['nuevo_stock']}")
                sku_almacen_in.value, cant_almacen_in.value, motivo_almacen_in.value = "", "1", "Ajuste de inventario"
                cargar_inventario()
            else: mostrar_mensaje(resp.json().get("detail", "Error en la operación."), True)
        except Exception as ex: mostrar_mensaje(f"Error de conexión: {ex}", True)

    def cargar_kardex():
        lista_kardex_ui.controls.clear()
        try:
            resp = requests.get(KARDEX_URL)
            if resp.status_code == 200:
                movs = resp.json()
                for m in movs:
                    col_tipo = "#10b981" if m['tipo_movimiento'] in ['ENTRADA', 'CREACIÓN'] else "#EF4444"
                    lista_kardex_ui.controls.append(
                        ft.Container(
                            bgcolor="#1f2937", padding=8, border_radius=6,
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(f"{m['fecha']} | SKU: {m['sku']}", color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
                                    ft.Text(m['motivo'], color="#9CA3AF", size=11)
                                ], expand=True),
                                ft.Text(f"{m['tipo_movimiento']} ({m['cantidad']})", color=col_tipo, size=11, weight=ft.FontWeight.BOLD)
                            ])
                        )
                    )
        except Exception: pass
        page.update()

    def cargar_alertas():
        lista_alertas_ui.controls.clear()
        try:
            resp = requests.get(ALERTAS_URL)
            if resp.status_code == 200:
                alertas = resp.json()
                if not alertas:
                    lista_alertas_ui.controls.append(ft.Text("✔️ Todo en orden. Sin stock crítico.", color="#10b981", size=12))
                for a in alertas:
                    lista_alertas_ui.controls.append(
                        ft.Container(
                            bgcolor="#371B1B", padding=8, border_radius=6,
                            content=ft.Row([
                                ft.Text(f"{a['nombre']} (SKU: {a['sku']})", color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
                                ft.Text(f"Stock: {a['stock']} / Min: {a['stock_minimo']}", color="#EF4444", size=12, weight=ft.FontWeight.BOLD)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        )
                    )
        except Exception: pass
        page.update()

    # --- VISTA LOGIN ---
    user_input = ft.TextField(label="Usuario", value="admin", border_color="#374151", focused_border_color="#10b981")
    pass_input = ft.TextField(label="Contraseña", value="admin123", password=True, can_reveal_password=True, border_color="#374151", focused_border_color="#10b981")
    lbl_login_error = ft.Text("", color=ft.Colors.RED_400, size=12)

    def ejecutar_login(e):
        username, password = user_input.value.strip(), pass_input.value.strip()
        if not username or not password:
            lbl_login_error.value = "Ingrese usuario y contraseña."
            lbl_login_error.color = ft.colors.RED_400
            page.update()
            return

        # Aviso visual mientras la instancia despierta
        lbl_login_error.value = "Conectando con el servidor en la nube... Espere un momento ⏳"
        lbl_login_error.color = ft.colors.AMBER_400
        page.update()

        try:
            # timeout=60 da margen suficiente para el 'cold start' de Render
            resp = requests.post(
                LOGIN_URL, 
                data={"username": username, "password": password}, 
                timeout=60
            )
            
            if resp.status_code == 200:
                data = resp.json()
                session["token"], session["username"] = data["access_token"], username
                session["nombre"], session["rol"] = data["nombre"], data["rol"]
                lbl_login_error.value = ""
                iniciar_panel_principal()
            elif resp.status_code == 400:
                lbl_login_error.color = ft.colors.RED_400
                lbl_login_error.value = "Usuario o contraseña incorrectos."
                page.update()
            else:
                lbl_login_error.color = ft.colors.RED_400
                lbl_login_error.value = f"Error del servidor ({resp.status_code}). Intente de nuevo."
                page.update()

        except requests.exceptions.Timeout:
            lbl_login_error.color = ft.colors.AMBER_400
            lbl_login_error.value = "El servidor estaba en reposo y está iniciando. Haga clic en Iniciar Sesión de nuevo."
            page.update()
        except Exception as ex:
            lbl_login_error.color = ft.colors.RED_400
            lbl_login_error.value = f"Error de conexión: {ex}"
            page.update()

    login_view = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.LOCK_PERSON, size=60, color="#10b981"),
            ft.Text("Inventario CDPS", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text("Acceso Administrador", size=14, color="#9CA3AF"),
            ft.Container(height=15),
            user_input,
            pass_input,
            lbl_login_error,
            ft.Container(height=10),
            ft.ElevatedButton("Iniciar Sesión", bgcolor="#059669", color=ft.Colors.WHITE, width=300, on_click=ejecutar_login)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.center,
        expand=True
    )

    # --- MONTAJE PANEL PRINCIPAL ---
    def iniciar_panel_principal():
        # LIMPIEZA CLAVE: Elimina controles viejos para no triplicar
        page.controls.clear()

        lbl_usuario_info = ft.Text(f"👤 {session['nombre']} ({session['rol']})", size=12, color="#34D399", weight=ft.FontWeight.BOLD)

        tabs_panel = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            scrollable=True,
            tabs=[
                ft.Tab(
                    text="Inventario",
                    icon=ft.Icons.INVENTORY,
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Row([lbl_usuario_info, ft.IconButton(icon=ft.Icons.REFRESH, icon_color="#34D399", on_click=lambda _: cargar_inventario())], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.ElevatedButton("📥 Cargar Excel (.xlsx)", bgcolor="#0284C7", color=ft.Colors.WHITE, width=420, on_click=lambda _: file_picker_excel.pick_files(allowed_extensions=["xlsx"])),
                            ft.Container(height=5),
                            lista_productos
                        ])
                    )
                ),
                ft.Tab(
                    text="Ventas POS",
                    icon=ft.Icons.POINT_OF_SALE,
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Text("🛒 Carrito de Venta", size=18, weight=ft.FontWeight.BOLD, color="#10b981"),
                            ft.Row([sku_venta_in, cant_venta_in], spacing=10),
                            ft.ElevatedButton("Agregar al Carrito", bgcolor="#059669", color=ft.Colors.WHITE, on_click=agregar_al_carrito, width=420),
                            ft.Divider(color="#374151"),
                            ft.Text("Artículos seleccionados:", size=13, weight=ft.FontWeight.BOLD, color="#9CA3AF"),
                            ft.Container(content=lista_carrito_ui, height=120),
                            ft.Divider(color="#374151"),
                            lbl_total_pagar,
                            metodo_pago_dropdown,
                            ft.Row([recibido_usd_in, recibido_bs_in], spacing=10),
                            lbl_vuelto_calc,
                            ft.Container(height=5),
                            cliente_in,
                            ft.Container(height=10),
                            ft.ElevatedButton("💵 Finalizar Venta", bgcolor="#2563EB", color=ft.Colors.WHITE, on_click=procesar_venta_pos, width=420),
                            ft.Container(height=20)
                        ], scroll=ft.ScrollMode.AUTO)
                    )
                ),
                ft.Tab(
                    text="Caja & Arqueo",
                    icon=ft.Icons.ACCOUNT_BALANCE_WALLET,
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Row([
                                ft.Text("💵 Tasa BCV", size=16, weight=ft.FontWeight.BOLD, color="#10b981"),
                                ft.Row([tasa_in, ft.IconButton(icon=ft.Icons.SAVE, icon_color="#10b981", on_click=actualizar_tasa)])
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(color="#374151"),
                            ft.Text("📊 Ventas del Día", size=16, weight=ft.FontWeight.BOLD, color="#10b981"),
                            lbl_total_dia_usd,
                            lbl_total_dia_bs,
                            ft.Container(height=5),
                            ft.Column([lbl_efectivo_usd, lbl_efectivo_bs, lbl_pago_movil, lbl_tarjeta], spacing=3),
                            ft.Divider(color="#374151"),
                            ft.Text("📑 Transacciones Registradas Hoy:", size=13, weight=ft.FontWeight.BOLD, color="#9CA3AF"),
                            ft.Container(content=lista_ventas_hoy_ui, height=140),
                            ft.Divider(color="#374151"),
                            ft.Text("🔒 Arqueo de Caja", size=16, weight=ft.FontWeight.BOLD, color="#EF4444"),
                            arq_efectivo_usd_in,
                            arq_efectivo_bs_in,
                            arq_obs_in,
                            ft.Container(height=10),
                            ft.ElevatedButton("📌 Realizar Cierre", bgcolor="#DC2626", color=ft.Colors.WHITE, on_click=procesar_cierre_caja, width=420),
                            ft.ElevatedButton("📄 Descargar PDF", bgcolor="#475569", color=ft.Colors.WHITE, on_click=descargar_pdf_cierre, width=420)
                        ], scroll=ft.ScrollMode.AUTO)
                    )
                ),
                ft.Tab(
                    text="Almacén",
                    icon=ft.Icons.WAREHOUSE,
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Text("📥 Carga y Salida", size=18, weight=ft.FontWeight.BOLD, color="#10b981"),
                            sku_almacen_in,
                            cant_almacen_in,
                            motivo_almacen_in,
                            ft.Container(height=10),
                            ft.Row([
                                ft.ElevatedButton("➕ Cargar", bgcolor="#059669", color=ft.Colors.WHITE, expand=True, on_click=lambda _: ejecutar_movimiento_stock(CARGA_URL, "Carga")),
                                ft.ElevatedButton("➖ Descargar", bgcolor="#DC2626", color=ft.Colors.WHITE, expand=True, on_click=lambda _: ejecutar_movimiento_stock(DESCARGA_URL, "Descarga"))
                            ], spacing=10),
                            ft.Divider(color="#374151"),
                            ft.ElevatedButton("🔄 Devolución", bgcolor="#D97706", color=ft.Colors.WHITE, width=420, on_click=abrir_modal_devolucion)
                        ], scroll=ft.ScrollMode.AUTO)
                    )
                ),
                ft.Tab(
                    text="Auditoría",
                    icon=ft.Icons.ASSESSMENT,
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Text("⚠️ Alertas de Bajo Stock", size=16, weight=ft.FontWeight.BOLD, color="#EF4444"),
                            ft.Container(content=lista_alertas_ui, height=120),
                            ft.Divider(color="#374151"),
                            ft.Text("📋 Kardex de Movimientos", size=16, weight=ft.FontWeight.BOLD, color="#10b981"),
                            ft.Container(content=lista_kardex_ui, height=220)
                        ], scroll=ft.ScrollMode.AUTO)
                    )
                ),
                ft.Tab(
                    text="Métricas",
                    icon=ft.Icons.BAR_CHART,
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            lbl_facturado_global,
                            ft.ElevatedButton("📊 Exportar Excel", bgcolor="#059669", color=ft.Colors.WHITE, width=420, on_click=descargar_reporte_excel),
                            ft.Divider(color="#374151"),
                            ft.Text("🏆 Top 5 Productos", size=14, weight=ft.FontWeight.BOLD, color="#9CA3AF"),
                            ft.Container(content=lista_top_productos_ui, height=130),
                            ft.Divider(color="#374151"),
                            ft.Text("📜 Historial Cierres:", size=14, weight=ft.FontWeight.BOLD, color="#9CA3AF"),
                            ft.Container(content=lista_cierres_ui, height=180)
                        ], scroll=ft.ScrollMode.AUTO)
                    )
                )
            ],
            expand=True
        )

        page.floating_action_button = ft.FloatingActionButton(
            icon=ft.Icons.ADD, bgcolor="#059669", on_click=abrir_modal_nuevo, tooltip="Registrar Producto"
        )

        cargar_tasa_bcv()
        cargar_inventario()
        cargar_ventas_hoy()
        cargar_kardex()
        cargar_alertas()
        cargar_estadisticas()
        
        page.add(tabs_panel)
        page.update()

    # Arranca únicamente mostrando el Login
    page.add(login_view)

if __name__ == "__main__":
    # Render asigna el puerto en la variable PORT (usualmente 10000)
    port_env = int(os.environ.get("PORT", 8550))
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=port_env
    )