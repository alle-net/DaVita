VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmPrincipal 
   Caption         =   "Registros"
   ClientHeight    =   8805.001
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   26880
   OleObjectBlob   =   "frmPrincipal.frx":0000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "frmPrincipal"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
' ============================================================
' frmPrincipal - Code-Behind
' Layout DINAMICO - ocupa 100% da area util do Excel
' Cole este codigo no VBA Editor:
'   ALT+F11 -> frmPrincipal (duplo clique) -> colar tudo
' ============================================================

Option Explicit

Private mDados() As Variant
Private mTotalLinhas As Long
Private mPaginaAtual As Long
Private Const REG_POR_PAGINA As Long = 50

Private mDictHospitais As Object
Private mDictRegionais As Object
Private mDictUnidades As Object
Private mDictStatus As Object
Private mDictMotivos As Object

Private Const COL_PCT As String = "6;10;10;10;10;7;7;7;10;9;6;6;2"

Private Sub UserForm_Initialize()
    Me.Caption = "Controle Financeiro"
    Me.StartUpPosition = 0
    AjustarLayout
    CarregarDimensoes
    CarregarDados
    lblUsuarioLogado.Caption = "Usuario: " & modAutenticacao.EmailAtual
End Sub

Private Sub AjustarLayout()
    Dim fW As Double, fH As Double
    Dim lbW As Double, lbH As Double, lbL As Double, lbT As Double
    Dim i As Integer, pcts() As String, p As Double, x As Double
    Dim cw As String

    fW = Application.UsableWidth * 1440 / Application.TwipsPerPixelX - 20
    fH = Application.UsableHeight * 1440 / Application.TwipsPerPixelY - 20
    Me.Width = fW
    Me.Height = fH
    Me.Left = 0
    Me.Top = 0

    lblUsuarioLogado.Left = 10
    lblUsuarioLogado.Top = 6
    lblUsuarioLogado.Width = fW * 0.4
    lblUsuarioLogado.Height = 20

    lblBuscar.Left = fW * 0.55
    lblBuscar.Top = 6
    lblBuscar.Width = 50
    lblBuscar.Height = 20

    txtBoxBusca.Left = fW * 0.55 + 55
    txtBoxBusca.Top = 4
    txtBoxBusca.Width = fW * 0.2
    txtBoxBusca.Height = 20

    lbL = 10
    lbT = 36
    lbW = fW - 20
    lbH = fH - 130

    lstDados.Left = lbL
    lstDados.Top = lbT + 18
    lstDados.Width = lbW
    lstDados.Height = lbH

    pcts = Split(COL_PCT, ";")
    For i = 0 To UBound(pcts)
        p = CLng(pcts(i)) / 100
        If cw <> "" Then cw = cw & ";"
        cw = cw & CInt((lbW - 15) * p)
    Next
    lstDados.ColumnCount = 13
    lstDados.ColumnWidths = cw

    Dim headers As Variant
    headers = Array("lblHdrCompetencia", "lblHdrRegional", "lblHdrUnidade", _
                    "lblHdrHospital", "lblHdrTitulo", "lblHdrNFe", _
                    "lblHdrStatusNFe", "lblHdrDataEnvio", "lblHdrMotivoGlosa", _
                    "lblHdrFaturamento", "lblHdrGlosa", "lblHdrPerda", _
                    "lblHdrObservacao")

    x = lbL
    For i = 0 To UBound(headers)
        p = CLng(pcts(i)) / 100
        With Me.Controls(headers(i))
            .Left = x
            .Width = (lbW - 15) * p
            .Top = lbT
            .Height = 16
        End With
        x = x + (lbW - 15) * p
    Next

    Dim btnY As Double: btnY = lbT + lbH + 4
    lblPagina.Left = lbL
    lblPagina.Top = btnY
    lblPagina.Width = 120
    lblPagina.Height = 18

    cmdAnterior.Left = lbL + 125
    cmdAnterior.Top = btnY - 2
    cmdAnterior.Width = 80
    cmdAnterior.Height = 22

    cmdProximo.Left = lbL + 210
    cmdProximo.Top = btnY - 2
    cmdProximo.Width = 80
    cmdProximo.Height = 22

    Dim btnRight As Double
    btnRight = fW - 10
    cmdAdicionar.Left = btnRight - 390
    cmdAdicionar.Top = btnY - 2
    cmdAdicionar.Width = 90
    cmdAdicionar.Height = 22

    cmbEditar.Left = btnRight - 290
    cmbEditar.Top = btnY - 2
    cmbEditar.Width = 90
    cmbEditar.Height = 22

    cmbExcluir.Left = btnRight - 190
    cmbExcluir.Top = btnY - 2
    cmbExcluir.Width = 90
    cmbExcluir.Height = 22

    Dim frameTop As Double: frameTop = btnY + 26
    Dim frameH As Double: frameH = fH - frameTop - 6
    Dim frameW As Double: frameW = (fW - 40) / 3

    fmeFaturamento.Left = 10
    fmeFaturamento.Top = frameTop
    fmeFaturamento.Width = frameW
    fmeFaturamento.Height = frameH

    fmeGlosa.Left = frameW + 20
    fmeGlosa.Top = frameTop
    fmeGlosa.Width = frameW
    fmeGlosa.Height = frameH

    fmePerda.Left = 2 * (frameW + 10) + 10
    fmePerda.Top = frameTop
    fmePerda.Width = frameW
    fmePerda.Height = frameH

    lblFaturamento.Left = 5
    lblFaturamento.Top = 16
    lblFaturamento.Width = frameW - 10
    lblFaturamento.Height = frameH - 20

    lblGlosa.Left = 5
    lblGlosa.Top = 16
    lblGlosa.Width = frameW - 10
    lblGlosa.Height = frameH - 20

    lblPerda.Left = 5
    lblPerda.Top = 16
    lblPerda.Width = frameW - 10
    lblPerda.Height = frameH - 20
End Sub

Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    If CloseMode = 0 Then
        If MsgBox("Deseja realmente sair do sistema?", vbQuestion + vbYesNo, "Sair") = vbNo Then
            Cancel = True
        Else
            modAutenticacao.ResetarSessao
        End If
    End If
End Sub

Private Sub CarregarDimensoes()
    Set mDictHospitais = modAutenticacao.ListarDimensao("Hospitais", "IdHospital", "Hospital")
    Set mDictRegionais = modAutenticacao.ListarDimensao("Regionais", "IdRegional", "Regional")
    Set mDictUnidades = modAutenticacao.ListarDimensao("Unidades", "IdUnidades", "Unidade")
    Set mDictStatus = modAutenticacao.ListarDimensao("StatusNFe", "IdStatus", "StatusNFe")
    Set mDictMotivos = modAutenticacao.ListarDimensao("MotivosGlosa", "IdMotivo", "MotivoGlosa")
End Sub

Private Sub CarregarDados()
    Dim vDados As Variant
    vDados = modAutenticacao.ListarDados
    If IsEmpty(vDados) Then
        mTotalLinhas = 0
        mPaginaAtual = 0
        AtualizarNavegacao
        ExibirTotalizadores
        Exit Sub
    End If
    mDados = vDados
    mTotalLinhas = UBound(mDados, 1)
    mPaginaAtual = 1
    AtualizarGrade
    AtualizarNavegacao
    ExibirTotalizadores
End Sub

Private Sub AtualizarGrade()
    lstDados.Clear
    If mTotalLinhas = 0 Then Exit Sub

    Dim primeiro As Long, ultimo As Long, i As Long
    primeiro = (mPaginaAtual - 1) * REG_POR_PAGINA + 1
    ultimo = primeiro + REG_POR_PAGINA - 1
    If ultimo > mTotalLinhas Then ultimo = mTotalLinhas

    Dim valores(0 To 12) As String
    For i = primeiro To ultimo
        valores(0) = FormatarData(mDados(i, 1))
        valores(1) = ResolverNome(mDictRegionais, mDados(i, 3))
        valores(2) = ResolverNome(mDictUnidades, mDados(i, 4))
        valores(3) = ResolverNome(mDictHospitais, mDados(i, 2))
        valores(4) = CStr(mDados(i, 5))
        valores(5) = CStr(mDados(i, 6))
        valores(6) = ResolverNome(mDictStatus, mDados(i, 7))
        valores(7) = FormatarData(mDados(i, 9))
        valores(8) = ResolverNome(mDictMotivos, mDados(i, 8))
        valores(9) = FormatarNumero(mDados(i, 10))
        valores(10) = FormatarNumero(mDados(i, 11))
        valores(11) = FormatarNumero(mDados(i, 12))
        valores(12) = CStr(mDados(i, 13))
        lstDados.AddItem Join(valores, vbTab)
    Next i
End Sub

Private Function ResolverNome(ByVal dict As Object, ByVal id As Variant) As String
    If dict Is Nothing Then
        ResolverNome = CStr(id)
    ElseIf dict.exists(id) Then
        ResolverNome = CStr(dict(id))
    Else
        ResolverNome = CStr(id)
    End If
End Function

Private Function FormatarData(ByVal v As Variant) As String
    If IsDate(v) Then
        FormatarData = Format(v, "dd/mm/yyyy")
    ElseIf IsNumeric(v) Then
        FormatarData = Format(CDate(v), "dd/mm/yyyy")
    Else
        FormatarData = ""
    End If
End Function

Private Function FormatarNumero(ByVal v As Variant) As String
    If IsNumeric(v) Then
        FormatarNumero = Format(CDec(v), "#,##0.00")
    Else
        FormatarNumero = "0,00"
    End If
End Function

Private Sub AtualizarNavegacao()
    If mTotalLinhas = 0 Then
        lblPagina.Caption = "0 registros"
        cmdAnterior.Enabled = False
        cmdProximo.Enabled = False
        Exit Sub
    End If
    Dim totalPag As Long
    totalPag = (mTotalLinhas + REG_POR_PAGINA - 1) \ REG_POR_PAGINA
    lblPagina.Caption = "Pagina " & mPaginaAtual & " de " & totalPag & _
                        " (" & mTotalLinhas & " registros)"
    cmdAnterior.Enabled = (mPaginaAtual > 1)
    cmdProximo.Enabled = (mPaginaAtual < totalPag)
End Sub

Private Sub ExibirTotalizadores()
    Dim somaFat As Currency, somaPerda As Currency, somaGlosa As Currency
    Dim i As Long

    If mTotalLinhas = 0 Then
        lblFaturamento.Caption = "0,00"
        lblGlosa.Caption = "0,00"
        lblPerda.Caption = "0,00"
        Exit Sub
    End If

    For i = 1 To mTotalLinhas
        If IsNumeric(mDados(i, 10)) Then somaFat = somaFat + CCur(mDados(i, 10))
        If IsNumeric(mDados(i, 11)) Then somaPerda = somaPerda + CCur(mDados(i, 11))
        If IsNumeric(mDados(i, 12)) Then somaGlosa = somaGlosa + CCur(mDados(i, 12))
    Next i

    lblFaturamento.Caption = Format(somaFat, "#,##0.00")
    lblPerda.Caption = Format(somaPerda, "#,##0.00")
    lblGlosa.Caption = Format(somaGlosa, "#,##0.00")
End Sub

Private Sub cmdAnterior_Click()
    If mPaginaAtual > 1 Then
        mPaginaAtual = mPaginaAtual - 1
        AtualizarGrade
        AtualizarNavegacao
    End If
End Sub

Private Sub cmdProximo_Click()
    Dim totalPag As Long
    totalPag = (mTotalLinhas + REG_POR_PAGINA - 1) \ REG_POR_PAGINA
    If mPaginaAtual < totalPag Then
        mPaginaAtual = mPaginaAtual + 1
        AtualizarGrade
        AtualizarNavegacao
    End If
End Sub

Private Sub txtBoxBusca_Change()
    Dim busca As String
    busca = Trim(txtBoxBusca.Value)
    If busca = "" Then
        CarregarDados
        Exit Sub
    End If

    Dim filtrados() As Variant
    Dim linha As Long, count As Long, i As Long, j As Long
    count = 0
    ReDim filtrados(1 To mTotalLinhas, 1 To 14)

    For i = 1 To mTotalLinhas
        For j = 1 To 13
            Dim cellVal As String
            cellVal = CStr(mDados(i, j))
            If LCase(cellVal) Like LCase("*" & busca & "*") Then
                count = count + 1
                For linha = 1 To 14
                    filtrados(count, linha) = mDados(i, linha)
                Next linha
                Exit For
            End If
        Next j
    Next i

    If count = 0 Then
        lstDados.Clear
        lblPagina.Caption = "Nenhum resultado encontrado"
        cmdAnterior.Enabled = False
        cmdProximo.Enabled = False
        lblFaturamento.Caption = "0,00"
        lblGlosa.Caption = "0,00"
        lblPerda.Caption = "0,00"
        Exit Sub
    End If

    mDados = filtrados
    mTotalLinhas = count
    mPaginaAtual = 1
    AtualizarGrade
    AtualizarNavegacao
    ExibirTotalizadores
End Sub


