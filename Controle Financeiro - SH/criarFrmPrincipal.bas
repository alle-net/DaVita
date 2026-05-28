Attribute VB_Name = "CriarFrmPrincipal"
Option Explicit

Public Sub CriarFrmPrincipal()
    On Error GoTo ErrHandler
    
    Dim vba As Object, fc As Object, d As Object, ct As Object
    
    Set vba = Application.VBE.ActiveVBProject
    For Each fc In vba.VBComponents
        If fc.Name = "frmPrincipal" Then vba.VBComponents.Remove fc: Exit For
    Next
    
    Set fc = vba.VBComponents.Add(3): fc.Name = "frmPrincipal"
    Set d = fc.Designer
    d.Caption = "Controle Financeiro SH"
    d.Width = 820: d.Height = 680: d.StartUpPosition = 0
    
    ' === Header ===
    Set ct = d.Controls.Add("Forms.Image.1", "imgLogo", True)
    ct.Left = 10: ct.Top = 15: ct.Width = 120: ct.Height = 50
    On Error Resume Next
    ct.Picture = LoadPicture(ThisWorkbook.Path & "\imagens\Logo.png")
    On Error GoTo ErrHandler
    
    Set ct = d.Controls.Add("Forms.Label.1", "lblTituloApp", True)
    ct.Caption = "Controle Financeiro"
    ct.Left = 140: ct.Top = 20: ct.Width = 640: ct.Height = 30
    ct.Font.Size = 18: ct.Font.Bold = True
    ct.TextAlign = 2

    Set ct = d.Controls.Add("Forms.Label.1", "lblUsuarioLogado", True)
    ct.Caption = "Usuário: --"
    ct.Left = 140: ct.Top = 50: ct.Width = 640: ct.Height = 16
    ct.Font.Size = 10: ct.TextAlign = 2
    ct.ForeColor = RGB(75, 75, 75)

    Set ct = d.Controls.Add("Forms.Label.1", "lblTopoLinha", True)
    ct.Caption = ""
    ct.Left = 10: ct.Top = 75: ct.Width = 800: ct.Height = 2
    ct.BackColor = RGB(210, 210, 210)
    
    ' === Grid ===
    Set ct = d.Controls.Add("Forms.ListBox.1", "lstGrid", True)
    ct.Left = 10: ct.Top = 95: ct.Width = 800: ct.Height = 260
    ct.ColumnCount = 16
    ct.ColumnWidths = "0;140;80;0;0;0;120;50;0;0;80;100;100;100;130;100"
    
    ' === Navigation ===
    Set ct = d.Controls.Add("Forms.Label.1", "lblPagina", True)
    ct.Caption = "Pagina 1 de 1 (0 registros)"
    ct.Left = 10: ct.Top = 365: ct.Width = 600: ct.Height = 20
    ct.Font.Size = 10
    
    Set ct = d.Controls.Add("Forms.CommandButton.1", "cmdAnterior", True)
    ct.Caption = "< &Anterior": ct.Left = 620: ct.Top = 363: ct.Width = 90: ct.Height = 24
    
    Set ct = d.Controls.Add("Forms.CommandButton.1", "cmdProximo", True)
    ct.Caption = "&Proximo >": ct.Left = 720: ct.Top = 363: ct.Width = 90: ct.Height = 24
    
    ' === Detail Fields - Row 1 ===
    Set ct = d.Controls.Add("Forms.Label.1", "lblCompetencia", True)
    ct.Caption = "Competencia:": ct.Left = 10: ct.Top = 405: ct.Width = 75: ct.Height = 15
    Set ct = d.Controls.Add("Forms.TextBox.1", "txtCompetencia", True)
    ct.Left = 85: ct.Top = 403: ct.Width = 120: ct.Height = 22
    
    Set ct = d.Controls.Add("Forms.Label.1", "lblTitulo", True)
    ct.Caption = "Titulo:": ct.Left = 220: ct.Top = 405: ct.Width = 40: ct.Height = 15
    Set ct = d.Controls.Add("Forms.TextBox.1", "txtTitulo", True)
    ct.Left = 265: ct.Top = 403: ct.Width = 200: ct.Height = 22
    
    Set ct = d.Controls.Add("Forms.Label.1", "lblNFe", True)
    ct.Caption = "NFe:": ct.Left = 485: ct.Top = 405: ct.Width = 30: ct.Height = 15
    Set ct = d.Controls.Add("Forms.TextBox.1", "txtNFe", True)
    ct.Left = 520: ct.Top = 403: ct.Width = 120: ct.Height = 22
    
    Set ct = d.Controls.Add("Forms.Label.1", "lblEnvioNFe", True)
    ct.Caption = "Envio NFe:": ct.Left = 650: ct.Top = 405: ct.Width = 70: ct.Height = 15
    Set ct = d.Controls.Add("Forms.TextBox.1", "txtEnvioNFe", True)
    ct.Left = 725: ct.Top = 403: ct.Width = 85: ct.Height = 22
    
    ' === Detail Fields - Row 2 ===
    Set ct = d.Controls.Add("Forms.Label.1", "lblHospital", True)
    ct.Caption = "Hospital:": ct.Left = 10: ct.Top = 445: ct.Width = 60: ct.Height = 15
    Set ct = d.Controls.Add("Forms.ComboBox.1", "cboHospital", True)
    ct.Left = 65: ct.Top = 443: ct.Width = 200: ct.Height = 22: ct.Style = 2
    
    Set ct = d.Controls.Add("Forms.Label.1", "lblRegional", True)
    ct.Caption = "Regional:": ct.Left = 280: ct.Top = 445: ct.Width = 55: ct.Height = 15
    Set ct = d.Controls.Add("Forms.ComboBox.1", "cboRegional", True)
    ct.Left = 335: ct.Top = 443: ct.Width = 170: ct.Height = 22: ct.Style = 2
    
    Set ct = d.Controls.Add("Forms.Label.1", "lblUnidade", True)
    ct.Caption = "Unidade:": ct.Left = 520: ct.Top = 445: ct.Width = 55: ct.Height = 15
    Set ct = d.Controls.Add("Forms.ComboBox.1", "cboUnidade", True)
    ct.Left = 575: ct.Top = 443: ct.Width = 190: ct.Height = 22: ct.Style = 2
    
    ' === Detail Fields - Row 3 ===
    Set ct = d.Controls.Add("Forms.Label.1", "lblValorFaturamento", True)
    ct.Caption = "Val. Faturamento:": ct.Left = 10: ct.Top = 485: ct.Width = 95: ct.Height = 15
    Set ct = d.Controls.Add("Forms.TextBox.1", "txtValorFaturamento", True)
    ct.Left = 110: ct.Top = 483: ct.Width = 100: ct.Height = 22
    
    Set ct = d.Controls.Add("Forms.Label.1", "lblValorPerda", True)
    ct.Caption = "Val. Perda:": ct.Left = 220: ct.Top = 485: ct.Width = 65: ct.Height = 15
    Set ct = d.Controls.Add("Forms.TextBox.1", "txtValorPerda", True)
    ct.Left = 285: ct.Top = 483: ct.Width = 100: ct.Height = 22
    
    Set ct = d.Controls.Add("Forms.Label.1", "lblValorGlosa", True)
    ct.Caption = "Val. Glosa:": ct.Left = 395: ct.Top = 485: ct.Width = 65: ct.Height = 15
    Set ct = d.Controls.Add("Forms.TextBox.1", "txtValorGlosa", True)
    ct.Left = 460: ct.Top = 483: ct.Width = 100: ct.Height = 22
    
    Set ct = d.Controls.Add("Forms.Label.1", "lblData", True)
    ct.Caption = "Data:": ct.Left = 570: ct.Top = 485: ct.Width = 40: ct.Height = 15
    Set ct = d.Controls.Add("Forms.TextBox.1", "txtData", True)
    ct.Left = 615: ct.Top = 483: ct.Width = 140: ct.Height = 22
    
    ' === Detail Fields - Row 4 (Observacao) ===
    Set ct = d.Controls.Add("Forms.Label.1", "lblObservacao", True)
    ct.Caption = "Observacao:": ct.Left = 10: ct.Top = 525: ct.Width = 75: ct.Height = 15
    Set ct = d.Controls.Add("Forms.TextBox.1", "txtObservacao", True)
    ct.Left = 10: ct.Top = 542: ct.Width = 760: ct.Height = 60
    ct.MultiLine = True: ct.WordWrap = True: ct.EnterKeyBehavior = True
    
    ' === Hidden ID field ===
    Set ct = d.Controls.Add("Forms.TextBox.1", "txtID", True)
    ct.Left = 0: ct.Top = 0: ct.Width = 0: ct.Height = 0
    
    ' === Action Buttons ===
    Set ct = d.Controls.Add("Forms.CommandButton.1", "cmdAdicionar", True)
    ct.Caption = "": ct.Left = 10: ct.Top = 620: ct.Width = 36: ct.Height = 36
    On Error Resume Next
    ct.Picture = LoadPicture(ThisWorkbook.Path & "\imagens\icon_add.bmp")
    ct.ControlTipText = "Adicionar"
    On Error GoTo ErrHandler
    
    Set ct = d.Controls.Add("Forms.CommandButton.1", "cmdEditar", True)
    ct.Caption = "": ct.Left = 56: ct.Top = 620: ct.Width = 36: ct.Height = 36
    On Error Resume Next
    ct.Picture = LoadPicture(ThisWorkbook.Path & "\imagens\icon_edit.bmp")
    ct.ControlTipText = "Editar"
    On Error GoTo ErrHandler
    
    Set ct = d.Controls.Add("Forms.CommandButton.1", "cmdExcluir", True)
    ct.Caption = "": ct.Left = 102: ct.Top = 620: ct.Width = 36: ct.Height = 36
    On Error Resume Next
    ct.Picture = LoadPicture(ThisWorkbook.Path & "\imagens\icon_remove.bmp")
    ct.ControlTipText = "Excluir"
    On Error GoTo ErrHandler
    
    Set ct = d.Controls.Add("Forms.CommandButton.1", "cmdLimpar", True)
    ct.Caption = "&Limpar": ct.Left = 150: ct.Top = 624: ct.Width = 90: ct.Height = 28
    
    AdicionarCodigoForm fc
    MsgBox "Formulario frmPrincipal criado com sucesso!", vbInformation, "Sucesso"
    Exit Sub
    
ErrHandler:
    MsgBox "Erro: " & Err.Description, vbCritical, "Erro " & Err.Number
End Sub

Private Sub AdicionarCodigoForm(fc As Object)
    Dim cm As Object: Set cm = fc.CodeModule
    
    cm.AddFromString "Option Explicit"
    cm.AddFromString "Private mSelectedRow As Long"
    cm.AddFromString ""
    
    ' === UserForm_Initialize ===
    cm.AddFromString "Private Sub UserForm_Initialize()"
    cm.AddFromString "    CarregarGrid"
    cm.AddFromString "    CarregarCombos"
    cm.AddFromString "    AtualizarUsuarioLogado"
    cm.AddFromString "    AtualizarNavegacao"
    cm.AddFromString "    Me.Left = (Application.Width - Me.Width) / 2"
    cm.AddFromString "    Me.Top = (Application.Height - Me.Height) / 2"
    cm.AddFromString "End Sub"
    cm.AddFromString ""
    
    ' === CarregarGrid ===
    cm.AddFromString "Private Sub CarregarGrid()"
    cm.AddFromString "    Dim dados As Variant"
    cm.AddFromString "    dados = modDados.GetPageDataFormatado"
    cm.AddFromString "    lstGrid.Clear"
    cm.AddFromString "    If Not IsArray(dados) Then Exit Sub"
    cm.AddFromString "    On Error Resume Next"
    cm.AddFromString "    If UBound(dados, 1) >= 0 Then lstGrid.List = dados"
    cm.AddFromString "    On Error GoTo 0"
    cm.AddFromString "End Sub"
    cm.AddFromString ""
    
    ' === CarregarCombos ===
    cm.AddFromString "Private Sub CarregarCombos()"
    cm.AddFromString "    Dim dados As Variant, i As Long"
    cm.AddFromString ""
    cm.AddFromString "    dados = modDados.CarregarDimensao(""Hospitais"", ""Hospitais"")"
    cm.AddFromString "    cboHospital.Clear"
    cm.AddFromString "    If (Not dados) = -1 Then GoTo prox1"
    cm.AddFromString "    For i = LBound(dados, 1) To UBound(dados, 1)"
    cm.AddFromString "        cboHospital.AddItem dados(i, 2)"
    cm.AddFromString "        cboHospital.ItemData(cboHospital.NewIndex) = CLng(dados(i, 1))"
    cm.AddFromString "    Next i"
    cm.AddFromString ""
    cm.AddFromString "prox1:"
    cm.AddFromString "    dados = modDados.CarregarDimensao(""Regionais"", ""Regionais"")"
    cm.AddFromString "    cboRegional.Clear"
    cm.AddFromString "    If (Not dados) = -1 Then GoTo prox2"
    cm.AddFromString "    For i = LBound(dados, 1) To UBound(dados, 1)"
    cm.AddFromString "        cboRegional.AddItem dados(i, 2)"
    cm.AddFromString "        cboRegional.ItemData(cboRegional.NewIndex) = CLng(dados(i, 1))"
    cm.AddFromString "    Next i"
    cm.AddFromString ""
    cm.AddFromString "prox2:"
    cm.AddFromString "    dados = modDados.CarregarDimensao(""Unidades"", ""Unidades"")"
    cm.AddFromString "    cboUnidade.Clear"
    cm.AddFromString "    If (Not dados) = -1 Then GoTo prox3"
    cm.AddFromString "    For i = LBound(dados, 1) To UBound(dados, 1)"
    cm.AddFromString "        cboUnidade.AddItem dados(i, 2)"
    cm.AddFromString "        cboUnidade.ItemData(cboUnidade.NewIndex) = CLng(dados(i, 1))"
    cm.AddFromString "    Next i"
    cm.AddFromString "prox3:"
    cm.AddFromString "End Sub"
    cm.AddFromString ""
    
    ' === Navegacao ===
    cm.AddFromString "Private Sub cmdAnterior_Click()"
    cm.AddFromString "    modDados.PreviousPage"
    cm.AddFromString "    CarregarGrid"
    cm.AddFromString "    AtualizarNavegacao"
    cm.AddFromString "End Sub"
    cm.AddFromString ""
    
    cm.AddFromString "Private Sub cmdProximo_Click()"
    cm.AddFromString "    modDados.NextPage"
    cm.AddFromString "    CarregarGrid"
    cm.AddFromString "    AtualizarNavegacao"
    cm.AddFromString "End Sub"
    cm.AddFromString ""
    
    cm.AddFromString "Private Sub AtualizarNavegacao()"
    cm.AddFromString "    If modDados.GetTotalRecords = 0 Then"
    cm.AddFromString "        lblPagina.Caption = \"Nenhum registro encontrado\""
    cm.AddFromString "    Else"
    cm.AddFromString "        lblPagina.Caption = modDados.GetPageInfo"
    cm.AddFromString "    End If"
    cm.AddFromString "    cmdAnterior.Enabled = (modDados.GetCurrentPage > 1)"
    cm.AddFromString "    cmdProximo.Enabled = (modDados.GetCurrentPage < modDados.GetTotalPages)"
    cm.AddFromString "End Sub"
    cm.AddFromString ""
    cm.AddFromString "Private Sub AtualizarUsuarioLogado()"
    cm.AddFromString "    If Trim(modAutenticacao.EmailAtual) = """ Then"
    cm.AddFromString "        lblUsuarioLogado.Caption = ""Usuário: --"""
    cm.AddFromString "    Else"
    cm.AddFromString "        lblUsuarioLogado.Caption = ""Usuário: "" & modAutenticacao.EmailAtual"
    cm.AddFromString "    End If"
    cm.AddFromString "End Sub"
    cm.AddFromString ""
    
    ' === Grid Click ===
    cm.AddFromString "Private Sub lstGrid_Click()"
    cm.AddFromString "    If lstGrid.ListIndex = -1 Then Exit Sub"
    cm.AddFromString "    Dim rowIdx As Long, vals As Variant, i As Long"
    cm.AddFromString "    rowIdx = modDados.GetRecordIdxAtGridRow(lstGrid.ListIndex + 1)"
    cm.AddFromString "    If rowIdx < 1 Then Exit Sub"
    cm.AddFromString "    vals = modDados.GetRecordByGlobalIdx(rowIdx)"
    cm.AddFromString "    If Not IsArray(vals) Then Exit Sub"
    cm.AddFromString "    txtID.Value = vals(1)"
    cm.AddFromString "    txtCompetencia.Value = vals(3)"
    cm.AddFromString "    txtTitulo.Value = vals(7)"
    cm.AddFromString "    txtNFe.Value = vals(8)"
    cm.AddFromString "    txtEnvioNFe.Value = vals(11)"
    cm.AddFromString "    txtValorFaturamento.Value = vals(12)"
    cm.AddFromString "    txtValorPerda.Value = vals(13)"
    cm.AddFromString "    txtValorGlosa.Value = vals(14)"
    cm.AddFromString "    txtObservacao.Value = vals(15)"
    cm.AddFromString "    txtData.Value = vals(16)"
    cm.AddFromString ""
    cm.AddFromString "    For i = 0 To cboHospital.ListCount - 1"
    cm.AddFromString "        If cboHospital.ItemData(i) = vals(4) Then cboHospital.ListIndex = i: Exit For"
    cm.AddFromString "    Next i"
    cm.AddFromString "    For i = 0 To cboRegional.ListCount - 1"
    cm.AddFromString "        If cboRegional.ItemData(i) = vals(5) Then cboRegional.ListIndex = i: Exit For"
    cm.AddFromString "    Next i"
    cm.AddFromString "    For i = 0 To cboUnidade.ListCount - 1"
    cm.AddFromString "        If cboUnidade.ItemData(i) = vals(6) Then cboUnidade.ListIndex = i: Exit For"
    cm.AddFromString "    Next i"
    cm.AddFromString "    mSelectedRow = rowIdx"
    cm.AddFromString "End Sub"
    cm.AddFromString ""
    
    ' === CRUD ===
    cm.AddFromString "Private Sub cmdAdicionar_Click()"
    cm.AddFromString "    Dim v(1 To 16) As Variant"
    cm.AddFromString "    v(2) = modAutenticacao.UsuarioAtual"
    cm.AddFromString "    v(3) = txtCompetencia.Value"
    cm.AddFromString "    v(4) = 0: If cboHospital.ListIndex >= 0 Then v(4) = cboHospital.ItemData(cboHospital.ListIndex)"
    cm.AddFromString "    v(5) = 0: If cboRegional.ListIndex >= 0 Then v(5) = cboRegional.ItemData(cboRegional.ListIndex)"
    cm.AddFromString "    v(6) = 0: If cboUnidade.ListIndex >= 0 Then v(6) = cboUnidade.ItemData(cboUnidade.ListIndex)"
    cm.AddFromString "    v(7) = txtTitulo.Value"
    cm.AddFromString "    v(8) = txtNFe.Value"
    cm.AddFromString "    v(9) = 0"
    cm.AddFromString "    v(10) = 0"
    cm.AddFromString "    v(11) = txtEnvioNFe.Value"
    cm.AddFromString "    v(12) = txtValorFaturamento.Value"
    cm.AddFromString "    v(13) = txtValorPerda.Value"
    cm.AddFromString "    v(14) = txtValorGlosa.Value"
    cm.AddFromString "    v(15) = txtObservacao.Value"
    cm.AddFromString "    v(16) = txtData.Value"
    cm.AddFromString "    If modDados.AdicionarRegistro(v) Then"
    cm.AddFromString "        modDados.CarregarDadosUsuario modAutenticacao.UsuarioAtual"
    cm.AddFromString "        CarregarGrid: AtualizarNavegacao: cmdLimpar_Click"
    cm.AddFromString "    Else"
    cm.AddFromString "        MsgBox ""Erro ao adicionar registro."", vbExclamation"
    cm.AddFromString "    End If"
    cm.AddFromString "End Sub"
    cm.AddFromString ""
    
    cm.AddFromString "Private Sub cmdEditar_Click()"
    cm.AddFromString "    If txtID.Value = """" Then MsgBox ""Selecione um registro."", vbExclamation: Exit Sub"
    cm.AddFromString "    Dim v(1 To 16) As Variant"
    cm.AddFromString "    v(2) = modAutenticacao.UsuarioAtual"
    cm.AddFromString "    v(3) = txtCompetencia.Value"
    cm.AddFromString "    v(4) = 0: If cboHospital.ListIndex >= 0 Then v(4) = cboHospital.ItemData(cboHospital.ListIndex)"
    cm.AddFromString "    v(5) = 0: If cboRegional.ListIndex >= 0 Then v(5) = cboRegional.ItemData(cboRegional.ListIndex)"
    cm.AddFromString "    v(6) = 0: If cboUnidade.ListIndex >= 0 Then v(6) = cboUnidade.ItemData(cboUnidade.ListIndex)"
    cm.AddFromString "    v(7) = txtTitulo.Value"
    cm.AddFromString "    v(8) = txtNFe.Value"
    cm.AddFromString "    v(9) = 0"
    cm.AddFromString "    v(10) = 0"
    cm.AddFromString "    v(11) = txtEnvioNFe.Value"
    cm.AddFromString "    v(12) = txtValorFaturamento.Value"
    cm.AddFromString "    v(13) = txtValorPerda.Value"
    cm.AddFromString "    v(14) = txtValorGlosa.Value"
    cm.AddFromString "    v(15) = txtObservacao.Value"
    cm.AddFromString "    v(16) = txtData.Value"
    cm.AddFromString "    If modDados.EditarRegistro(txtID.Value, v) Then"
    cm.AddFromString "        modDados.CarregarDadosUsuario modAutenticacao.UsuarioAtual"
    cm.AddFromString "        CarregarGrid: AtualizarNavegacao: cmdLimpar_Click"
    cm.AddFromString "    Else"
    cm.AddFromString "        MsgBox ""Erro ao editar registro."", vbExclamation"
    cm.AddFromString "    End If"
    cm.AddFromString "End Sub"
    cm.AddFromString ""
    
    cm.AddFromString "Private Sub cmdExcluir_Click()"
    cm.AddFromString "    If txtID.Value = """" Then MsgBox ""Selecione um registro."", vbExclamation: Exit Sub"
    cm.AddFromString "    If MsgBox(""Excluir registro?"", vbQuestion + vbYesNo) <> vbYes Then Exit Sub"
    cm.AddFromString "    If modDados.ExcluirRegistro(txtID.Value) Then"
    cm.AddFromString "        modDados.CarregarDadosUsuario modAutenticacao.UsuarioAtual"
    cm.AddFromString "        CarregarGrid: AtualizarNavegacao: cmdLimpar_Click"
    cm.AddFromString "    Else"
    cm.AddFromString "        MsgBox ""Erro ao excluir registro."", vbExclamation"
    cm.AddFromString "    End If"
    cm.AddFromString "End Sub"
    cm.AddFromString ""
    
    cm.AddFromString "Private Sub cmdLimpar_Click()"
    cm.AddFromString "    txtID.Value = """": txtCompetencia.Value = """": txtTitulo.Value = """""
    cm.AddFromString "    txtNFe.Value = """": txtEnvioNFe.Value = """": txtValorFaturamento.Value = """""
    cm.AddFromString "    txtValorPerda.Value = """": txtValorGlosa.Value = """""
    cm.AddFromString "    txtObservacao.Value = """": txtData.Value = """""
    cm.AddFromString "    cboHospital.ListIndex = -1: cboRegional.ListIndex = -1: cboUnidade.ListIndex = -1"
    cm.AddFromString "    mSelectedRow = 0"
    cm.AddFromString "End Sub"
    cm.AddFromString ""
    
    ' === QueryClose ===
    cm.AddFromString "Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)"
    cm.AddFromString "    If CloseMode = 0 Then Cancel = 1"
    cm.AddFromString "End Sub"
End Sub
