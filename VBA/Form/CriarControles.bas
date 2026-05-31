Attribute VB_Name = "CriarControles"
Sub CriarControlesFrmPrincipal()
Dim frm As Object
Set frm = ThisWorkbook.VBProject.VBComponents("frmPrincipal").Designer
Dim i As Long
For i = frm.Controls.Count - 1 To 0 Step -1
    frm.Controls.Remove i
Next i
Dim img As Object
Set img = frm.Controls.Add("Forms.Image.1", "imgLogofrmPrincipal")
img.Left = 20: img.Top = 20: img.Width = 200: img.Height = 60
img.PictureSizeMode = 3
Dim lbl As Object
Set lbl = frm.Controls.Add("Forms.Label.1", "lblTitulo")
lbl.Caption = "Controle Financeiro SH"
lbl.Left = 220: lbl.Top = 30: lbl.Width = 500: lbl.Height = 35
lbl.Font.Size = 18: lbl.Font.Bold = True
lbl.ForeColor = RGB(0, 118, 182)
Set lbl = frm.Controls.Add("Forms.Label.1", "lblUsuarioLogado")
lbl.Caption = "Usuario:": lbl.Left = 870: lbl.Top = 35: lbl.Width = 300: lbl.Height = 20
lbl.TextAlign = 1
Set lbl = frm.Controls.Add("Forms.Label.1", "lblFiltrar")
lbl.Caption = "Filtrar:": lbl.Left = 20: lbl.Top = 100: lbl.Width = 50: lbl.Height = 20
Dim txt As Object
Set txt = frm.Controls.Add("Forms.TextBox.1", "txtBoxFiltro")
txt.Left = 75: txt.Top = 100: txt.Width = 300: txt.Height = 25
Dim btn As Object
Set btn = frm.Controls.Add("Forms.CommandButton.1", "cmdAtualizar")
btn.Caption = "Atualizar": btn.Left = 390: btn.Top = 100: btn.Width = 90: btn.Height = 25
Dim hdr As Object
Set hdr = frm.Controls.Add("Forms.Label.1", "lblHdrCompetencia")
hdr.Caption = "Competencia": hdr.Left = 20: hdr.Top = 135: hdr.Width = 65: hdr.Height = 18
hdr.Font.Size = 8: hdr.Font.Bold = True: hdr.ForeColor = RGB(0, 118, 182)
Set hdr = frm.Controls.Add("Forms.Label.1", "lblHdrTitulo")
hdr.Caption = "Titulo": hdr.Left = 85: hdr.Top = 135: hdr.Width = 120: hdr.Height = 18
hdr.Font.Size = 8: hdr.Font.Bold = True: hdr.ForeColor = RGB(0, 118, 182)
Set hdr = frm.Controls.Add("Forms.Label.1", "lblHdrNFe")
hdr.Caption = "NFe": hdr.Left = 205: hdr.Top = 135: hdr.Width = 70: hdr.Height = 18
hdr.Font.Size = 8: hdr.Font.Bold = True: hdr.ForeColor = RGB(0, 118, 182)
Set hdr = frm.Controls.Add("Forms.Label.1", "lblHdrEnvioNFe")
hdr.Caption = "Envio NFe": hdr.Left = 275: hdr.Top = 135: hdr.Width = 70: hdr.Height = 18
hdr.Font.Size = 8: hdr.Font.Bold = True: hdr.ForeColor = RGB(0, 118, 182)
Set hdr = frm.Controls.Add("Forms.Label.1", "lblHdrFaturamento")
hdr.Caption = "Faturamento": hdr.Left = 345: hdr.Top = 135: hdr.Width = 85: hdr.Height = 18
hdr.Font.Size = 8: hdr.Font.Bold = True: hdr.ForeColor = RGB(0, 118, 182)
Set hdr = frm.Controls.Add("Forms.Label.1", "lblHdrPerda")
hdr.Caption = "Perda": hdr.Left = 430: hdr.Top = 135: hdr.Width = 85: hdr.Height = 18
hdr.Font.Size = 8: hdr.Font.Bold = True: hdr.ForeColor = RGB(0, 118, 182)
Set hdr = frm.Controls.Add("Forms.Label.1", "lblHdrGlosa")
hdr.Caption = "Glosa": hdr.Left = 515: hdr.Top = 135: hdr.Width = 85: hdr.Height = 18
hdr.Font.Size = 8: hdr.Font.Bold = True: hdr.ForeColor = RGB(0, 118, 182)
Set hdr = frm.Controls.Add("Forms.Label.1", "lblHdrObservacao")
hdr.Caption = "Observacao": hdr.Left = 600: hdr.Top = 135: hdr.Width = 100: hdr.Height = 18
hdr.Font.Size = 8: hdr.Font.Bold = True: hdr.ForeColor = RGB(0, 118, 182)
Dim lst As Object
Set lst = frm.Controls.Add("Forms.ListBox.1", "lstDados")
lst.Left = 20: lst.Top = 156: lst.Width = 1200: lst.Height = 370
Set btn = frm.Controls.Add("Forms.CommandButton.1", "cmdAnterior")
btn.Caption = "< Anterior": btn.Left = 30: btn.Top = 550: btn.Width = 90: btn.Height = 25
Set lbl = frm.Controls.Add("Forms.Label.1", "lblPagina")
lbl.Caption = "Pagina 0 de 0 (0 registros)"
lbl.Left = 140: lbl.Top = 550: lbl.Width = 600: lbl.Height = 25
lbl.TextAlign = 2
lbl.Font.Size = 10
Set btn = frm.Controls.Add("Forms.CommandButton.1", "cmdProximo")
btn.Caption = "Proximo >": btn.Left = 760: btn.Top = 550: btn.Width = 90: btn.Height = 25
Set btn = frm.Controls.Add("Forms.CommandButton.1", "cmdAdd")
btn.Caption = "Adicionar": btn.Left = 890: btn.Top = 550: btn.Width = 90: btn.Height = 25
Set btn = frm.Controls.Add("Forms.CommandButton.1", "cmdEditar")
btn.Caption = "Editar": btn.Left = 990: btn.Top = 550: btn.Width = 90: btn.Height = 25
Set btn = frm.Controls.Add("Forms.CommandButton.1", "cmdExcluir")
btn.Caption = "Excluir": btn.Left = 1090: btn.Top = 550: btn.Width = 90: btn.Height = 25
Set lbl = frm.Controls.Add("Forms.Label.1", "lblTituloFat")
lbl.Caption = "Faturamento": lbl.Left = 20: lbl.Top = 600: lbl.Width = 160: lbl.Height = 15
lbl.ForeColor = RGB(0, 118, 182): lbl.Font.Size = 9: lbl.Font.Bold = True
Set lbl = frm.Controls.Add("Forms.Label.1", "lblTituloGlosa")
lbl.Caption = "Glosa": lbl.Left = 460: lbl.Top = 600: lbl.Width = 160: lbl.Height = 15
lbl.ForeColor = RGB(0, 118, 182): lbl.Font.Size = 9: lbl.Font.Bold = True
Set lbl = frm.Controls.Add("Forms.Label.1", "lblTituloPerda")
lbl.Caption = "Perda": lbl.Left = 900: lbl.Top = 600: lbl.Width = 160: lbl.Height = 15
lbl.ForeColor = RGB(0, 118, 182): lbl.Font.Size = 9: lbl.Font.Bold = True
Set lbl = frm.Controls.Add("Forms.Label.1", "lblFaturamento")
lbl.Caption = "R$ 0,00": lbl.Left = 20: lbl.Top = 618: lbl.Width = 180: lbl.Height = 25
lbl.Font.Bold = True: lbl.Font.Size = 14
lbl.ForeColor = RGB(0, 118, 182)
Set lbl = frm.Controls.Add("Forms.Label.1", "lblGlosa")
lbl.Caption = "R$ 0,00": lbl.Left = 460: lbl.Top = 618: lbl.Width = 180: lbl.Height = 25
lbl.Font.Bold = True: lbl.Font.Size = 14
lbl.ForeColor = RGB(0, 118, 182)
Set lbl = frm.Controls.Add("Forms.Label.1", "lblPerda")
lbl.Caption = "R$ 0,00": lbl.Left = 900: lbl.Top = 618: lbl.Width = 180: lbl.Height = 25
lbl.Font.Bold = True: lbl.Font.Size = 14
lbl.ForeColor = RGB(0, 118, 182)
MsgBox "OK", vbInformation, "Setup"
End Sub
