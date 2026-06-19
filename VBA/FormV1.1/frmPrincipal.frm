VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmPrincipal 
   Caption         =   "Registros"
   ClientHeight    =   8235.001
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   20760
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
' Cole este codigo no VBA Editor:
'   ALT+F11 -> frmPrincipal (duplo clique) -> colar tudo
' ============================================================

Option Explicit

' === API Windows (32/64 bits) ===
#If VBA7 Then
Private Declare PtrSafe Function FindWindow Lib "user32" Alias "FindWindowA" _
    (ByVal lpClassName As String, ByVal lpWindowName As String) As LongPtr
Private Declare PtrSafe Function SetParent Lib "user32" _
    (ByVal hWndChild As LongPtr, ByVal hWndNewParent As LongPtr) As LongPtr
Private Declare PtrSafe Function ReleaseCapture Lib "user32" () As Long
Private Declare PtrSafe Function SendMessage Lib "user32" Alias "SendMessageA" _
    (ByVal hwnd As LongPtr, ByVal wMsg As Long, ByVal wParam As LongPtr, ByVal lParam As LongPtr) As LongPtr
Private Declare PtrSafe Function SetWindowLong Lib "user32" Alias "SetWindowLongA" _
    (ByVal hwnd As LongPtr, ByVal nIndex As Long, ByVal dwNewLong As Long) As Long
Private Declare PtrSafe Function GetWindowLong Lib "user32" Alias "GetWindowLongA" _
    (ByVal hwnd As LongPtr, ByVal nIndex As Long) As Long
#Else
Private Declare Function FindWindow Lib "user32" Alias "FindWindowA" _
    (ByVal lpClassName As String, ByVal lpWindowName As String) As Long
Private Declare Function SetParent Lib "user32" _
    (ByVal hWndChild As Long, ByVal hWndNewParent As Long) As Long
Private Declare Function ReleaseCapture Lib "user32" () As Long
Private Declare Function SendMessage Lib "user32" Alias "SendMessageA" _
    (ByVal hwnd As Long, ByVal wMsg As Long, ByVal wParam As Long, ByVal lParam As Long) As Long
Private Declare Function SetWindowLong Lib "user32" Alias "SetWindowLongA" _
    (ByVal hwnd As Long, ByVal nIndex As Long, ByVal dwNewLong As Long) As Long
Private Declare Function GetWindowLong Lib "user32" Alias "GetWindowLongA" _
    (ByVal hwnd As Long, ByVal nIndex As Long) As Long
#End If

Private Const GWL_STYLE As Long = (-16)
Private Const WM_NCLBUTTONDOWN As Long = &HA1
Private Const HTCAPTION As Long = 2
Private Const WS_CHILD As Long = &H40000000
Private Const WS_POPUP As Long = &H80000000
Private Const WS_CAPTION As Long = &HC00000
Private Const WS_THICKFRAME As Long = &H40000
Private Const WS_SYSMENU As Long = &H80000
Private Const WS_MINIMIZEBOX As Long = &H20000
Private Const WS_MAXIMIZEBOX As Long = &H10000

Private Const POR_PAGINA As Long = 50

Private Const NOME_TAB_DADOS As String = "TabDados"
Private Const NOME_TAB_HOSPITAIS As String = "TabHospitais"
Private Const NOME_TAB_REGIONAIS As String = "TabRegionais"
Private Const NOME_TAB_UNIDADES As String = "TabUnidades"
Private Const NOME_TAB_STATUS As String = "TabStatusNFe"
Private Const NOME_TAB_MOTIVOS As String = "TabMotivosGlosa"

' === Variaveis ===
Private mDados() As Variant
Private mFiltrados() As Variant
Private mTotalLinhas As Long
Private mTotalFiltrados As Long
Private mPaginaAtual As Long
Private mTotalPaginas As Long

Private mDictHospitais As Object
Private mDictRegionais As Object
Private mDictUnidades As Object
Private mDictStatusNFe As Object
Private mDictMotivos As Object

Private mNomesHeaders As Variant
Private mProporcoesColunas As Variant

' ====================================================================
' EVENTOS DO FORMULARIO
' ====================================================================

Private Sub UserForm_Initialize()
    Me.Caption = "Controle Financeiro"
    Me.StartUpPosition = 0
    Me.KeyPreview = True

    AnexarAoExcel

    lblUsuarioLogado.Caption = "Usu�rio: " & modAutenticacao.EmailAtual

    mNomesHeaders = Array( _
        "lblHdrCompetencia", "lblHdrRegional", "lblHdrUnidade", _
        "lblHdrHospital", "lblHdrTitulo", "lblHdrNFe", _
        "lblHdrStatusNFe", "lblHdrDataEnvio", "lblHdrMotivoGlosa", _
        "lblHdrFaturamento", "lblHdrGlosa", "lblHdrPerda", _
        "lblHdrObservacao")

    mProporcoesColunas = Array(70, 90, 90, 100, 130, 80, 70, 75, 90, 85, 75, 75, 150)

    lstDados.ColumnCount = 13
End Sub

Private Sub imgLogofrmPrincipal_MouseDown(ByVal Button As Integer, ByVal Shift As Integer, ByVal X As Single, ByVal Y As Single)
    IniciarArraste
End Sub

Private Sub lblUsuarioLogado_MouseDown(ByVal Button As Integer, ByVal Shift As Integer, ByVal X As Single, ByVal Y As Single)
    IniciarArraste
End Sub

Private Sub UserForm_Activate()
    Static bInicializado As Boolean
    AnexarAoExcel
    If Not bInicializado Then
        bInicializado = True
        AjustarTamanho
        CarregarCacheDimensoes
        CarregarDados
        ' Redimensionamento monitorado via Workbook_WindowResize
    End If
End Sub

Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    If CloseMode = 0 Then
        Cancel = True
        If MsgBox("Deseja realmente sair do sistema?", vbQuestion + vbYesNo, "Sair") = vbYes Then
            modAutenticacao.ResetarSessao
            ThisWorkbook.Close False
        End If
    End If
End Sub

Private Sub UserForm_KeyDown(ByVal KeyCode As MSForms.ReturnInteger, ByVal Shift As Integer)
    If KeyCode = vbKeyEscape Then
        KeyCode = 0
        FecharPainel
    End If
End Sub

' ====================================================================
' REDIMENSIONAMENTO
' ====================================================================

Public Sub AjustarTamanho()
    On Error Resume Next
    Me.StartUpPosition = 0
    Me.Width = Application.UsableWidth
    Me.Height = Application.UsableHeight
    Me.Left = 0
    Me.Top = 0
    On Error GoTo 0
    AjustarHeaders
End Sub

Private Sub AjustarHeaders()
    If lstDados Is Nothing Then Exit Sub
    If lstDados.Width = 0 Then Exit Sub

    Dim props As Variant, i As Long
    props = mProporcoesColunas

    Dim totalProp As Double
    For i = 0 To UBound(props)
        totalProp = totalProp + props(i)
    Next

    Dim larguraUtil As Double
    larguraUtil = lstDados.Width - 5

    Dim factor As Double
    factor = larguraUtil / totalProp

    Dim widths As String
    Dim leftPos As Double
    leftPos = lstDados.Left + 2

    For i = 0 To UBound(props)
        Dim w As Double
        w = props(i) * factor

        If widths <> "" Then widths = widths & ";"
        widths = widths & CStr(w)

        Dim hdr As Object
        Set hdr = Me.Controls(mNomesHeaders(i))
        hdr.Left = leftPos
        hdr.Width = w
        leftPos = leftPos + w
    Next

    lstDados.ColumnWidths = widths
End Sub

Private Sub IniciarArraste()
    Dim hwnd As LongPtr
    hwnd = FindWindow("ThunderDFrame", Me.Caption)
    If hwnd = 0 Then Exit Sub

    ReleaseCapture
    SendMessage hwnd, WM_NCLBUTTONDOWN, HTCAPTION, 0
End Sub

Private Sub AnexarAoExcel()
    #If VBA7 Then
        Dim hwndForm As LongPtr, hwndExcel As LongPtr
    #Else
        Dim hwndForm As Long, hwndExcel As Long
    #End If

    hwndForm = FindWindow("ThunderDFrame", Me.Caption)
    If hwndForm = 0 Then Exit Sub

    hwndExcel = FindWindow("XLMAIN", 0&)
    If hwndExcel = 0 Then Exit Sub

    Dim lStyle As Long
    lStyle = GetWindowLong(hwndForm, GWL_STYLE)
    lStyle = lStyle And Not WS_POPUP
    lStyle = lStyle Or WS_CHILD
    SetWindowLong hwndForm, GWL_STYLE, lStyle

    SetParent hwndForm, hwndExcel
End Sub

Private Sub FecharPainel()
    On Error Resume Next
    Unload Me
    On Error GoTo 0
End Sub

' ====================================================================
' CACHE DE DIMENSOES
' ====================================================================

Private Sub CarregarCacheDimensoes()
    Set mDictHospitais = CreateObject("Scripting.Dictionary")
    Set mDictRegionais = CreateObject("Scripting.Dictionary")
    Set mDictUnidades = CreateObject("Scripting.Dictionary")
    Set mDictStatusNFe = CreateObject("Scripting.Dictionary")
    Set mDictMotivos = CreateObject("Scripting.Dictionary")

    Dim conn As Object
    Set conn = modAutenticacao.AbrirConexao()
    If conn Is Nothing Then Exit Sub

    CarregarDicionario conn, NOME_TAB_HOSPITAIS, mDictHospitais
    CarregarDicionario conn, NOME_TAB_REGIONAIS, mDictRegionais
    CarregarDicionario conn, NOME_TAB_UNIDADES, mDictUnidades
    CarregarDicionario conn, NOME_TAB_STATUS, mDictStatusNFe
    CarregarDicionario conn, NOME_TAB_MOTIVOS, mDictMotivos

    modAutenticacao.FecharConexao conn
End Sub

Private Sub CarregarDicionario(ByVal conn As Object, ByVal nomeTabela As String, ByRef dict As Object)
    Dim rs As Object
    Set rs = modAutenticacao.ExecutarSelect(conn, "SELECT * FROM [" & nomeTabela & "]")
    If rs Is Nothing Then Exit Sub
    If rs.EOF Then
        rs.Close
        Exit Sub
    End If

    Do While Not rs.EOF
        Dim id As Variant
        id = rs.Fields(0).Value
        Dim nome As Variant
        nome = rs.Fields(1).Value
        If Not IsNull(id) And Not IsNull(nome) Then
            If Not dict.Exists(id) Then
                dict.Add id, nome
            End If
        End If
        rs.MoveNext
    Loop
    rs.Close
End Sub

Private Function ResolverNome(ByRef dict As Object, ByVal id As Variant) As String
    If Not IsNull(id) And Not IsEmpty(id) Then
        If dict.Exists(id) Then
            ResolverNome = dict(id)
            Exit Function
        End If
    End If
    ResolverNome = ""
End Function

' ====================================================================
' CARREGAMENTO DE DADOS
' ====================================================================

Private Sub CarregarDados()
    Dim conn As Object
    Set conn = modAutenticacao.AbrirConexao()
    If conn Is Nothing Then Exit Sub

    Dim sql As String
    sql = "SELECT * FROM [" & NOME_TAB_DADOS & "] WHERE IdUsuario = " & modAutenticacao.UsuarioAtual

    Dim rs As Object
    Set rs = modAutenticacao.ExecutarSelect(conn, sql)
    If rs Is Nothing Then
        modAutenticacao.FecharConexao conn
        Exit Sub
    End If

    Dim linhas As Collection
    Set linhas = New Collection
    Dim rowArr As Variant

    Do While Not rs.EOF
        rowArr = Array( _
            rs.Fields(2).Value, _
            rs.Fields(4).Value, _
            rs.Fields(5).Value, _
            rs.Fields(3).Value, _
            rs.Fields(6).Value, _
            rs.Fields(7).Value, _
            rs.Fields(8).Value, _
            rs.Fields(10).Value, _
            rs.Fields(9).Value, _
            rs.Fields(11).Value, _
            rs.Fields(13).Value, _
            rs.Fields(12).Value, _
            rs.Fields(14).Value)
        linhas.Add rowArr
        rs.MoveNext
    Loop

    rs.Close
    modAutenticacao.FecharConexao conn

    mTotalLinhas = linhas.Count

    If mTotalLinhas = 0 Then
        ReDim mDados(1 To 1, 0 To 12)
        mFiltrados = mDados
        mTotalFiltrados = 0
        AplicarFiltro
        Exit Sub
    End If

    ReDim mDados(1 To mTotalLinhas, 0 To 12)

    Dim idx As Long, j As Long, comp As Variant
    For idx = 1 To mTotalLinhas
        rowArr = linhas(idx)

        comp = rowArr(0)
        If IsDate(comp) Then
            mDados(idx, 0) = Format(comp, "dd/mm/yyyy")
        Else
            mDados(idx, 0) = comp
        End If

        mDados(idx, 1) = ResolverNome(mDictRegionais, rowArr(1))
        mDados(idx, 2) = ResolverNome(mDictUnidades, rowArr(2))
        mDados(idx, 3) = ResolverNome(mDictHospitais, rowArr(3))
        mDados(idx, 4) = rowArr(4)

        If Not IsNull(rowArr(5)) Then
            mDados(idx, 5) = CStr(rowArr(5))
        Else
            mDados(idx, 5) = ""
        End If

        mDados(idx, 6) = ResolverNome(mDictStatusNFe, rowArr(6))

        If IsDate(rowArr(7)) Then
            mDados(idx, 7) = Format(rowArr(7), "dd/mm/yyyy")
        Else
            mDados(idx, 7) = ""
        End If

        mDados(idx, 8) = ResolverNome(mDictMotivos, rowArr(8))

        If IsNumeric(rowArr(9)) Then
            mDados(idx, 9) = Round(rowArr(9), 2)
        Else
            mDados(idx, 9) = 0
        End If

        If IsNumeric(rowArr(10)) Then
            mDados(idx, 10) = Round(rowArr(10), 2)
        Else
            mDados(idx, 10) = 0
        End If

        If IsNumeric(rowArr(11)) Then
            mDados(idx, 11) = Round(rowArr(11), 2)
        Else
            mDados(idx, 11) = 0
        End If

        mDados(idx, 12) = rowArr(12)
    Next

    mFiltrados = mDados
    mTotalFiltrados = mTotalLinhas

    AplicarFiltro
End Sub

' ====================================================================
' FILTRO / BUSCA
' ====================================================================

Private Sub AplicarFiltro()
    Dim busca As String
    busca = LCase(Trim(txtBoxBusca.Value))

    If mTotalLinhas = 0 Then
        mTotalFiltrados = 0
        mPaginaAtual = 1
        CalcularPaginas
        PopularListBox
        AtualizarSomas
        Exit Sub
    End If

    If busca = "" Then
        mFiltrados = mDados
        mTotalFiltrados = mTotalLinhas
    Else
        Dim i As Long, j As Long, idx As Long
        idx = 0
        For i = 1 To mTotalLinhas
            For j = 0 To 12
                If InStr(LCase(CStr(mDados(i, j))), busca) > 0 Then
                    idx = idx + 1
                    Exit For
                End If
            Next
        Next

        If idx = 0 Then
            mTotalFiltrados = 0
        Else
            ReDim mFiltrados(1 To idx, 0 To 12)
            Dim dest As Long
            dest = 0
            For i = 1 To mTotalLinhas
                For j = 0 To 12
                    If InStr(LCase(CStr(mDados(i, j))), busca) > 0 Then
                        dest = dest + 1
                        Dim k As Long
                        For k = 0 To 12
                            mFiltrados(dest, k) = mDados(i, k)
                        Next
                        Exit For
                    End If
                Next
            Next
            mTotalFiltrados = idx
        End If
    End If

    mPaginaAtual = 1
    CalcularPaginas
    PopularListBox
    AtualizarSomas
End Sub

Private Sub txtBoxBusca_Change()
    AplicarFiltro
End Sub

' ====================================================================
' PAGINACAO
' ====================================================================

Private Sub CalcularPaginas()
    If mTotalFiltrados = 0 Then
        mTotalPaginas = 1
    Else
        mTotalPaginas = Int((mTotalFiltrados - 1) / POR_PAGINA) + 1
    End If
    If mPaginaAtual > mTotalPaginas Then mPaginaAtual = mTotalPaginas
    If mPaginaAtual < 1 Then mPaginaAtual = 1
End Sub

Private Sub PopularListBox()
    If mTotalFiltrados = 0 Then
        lstDados.Clear
        lblPagina.Caption = "0 de 0"
        cmdAnterior.Enabled = False
        cmdProximo.Enabled = False
        Exit Sub
    End If

    Dim inicio As Long
    inicio = (mPaginaAtual - 1) * POR_PAGINA + 1

    Dim fim As Long
    fim = inicio + POR_PAGINA - 1
    If fim > mTotalFiltrados Then fim = mTotalFiltrados

    Dim qtd As Long
    qtd = fim - inicio + 1

    Dim arr() As Variant
    ReDim arr(1 To qtd, 0 To 12)

    Dim i As Long, j As Long, idx As Long
    idx = 1
    For i = inicio To fim
        For j = 0 To 12
            arr(idx, j) = mFiltrados(i, j)
        Next
        idx = idx + 1
    Next

    lstDados.List = arr

    lblPagina.Caption = mPaginaAtual & " de " & mTotalPaginas
    cmdAnterior.Enabled = (mPaginaAtual > 1)
    cmdProximo.Enabled = (mPaginaAtual < mTotalPaginas)
End Sub

Private Sub cmdAnterior_Click()
    If mPaginaAtual > 1 Then
        mPaginaAtual = mPaginaAtual - 1
        PopularListBox
    End If
End Sub

Private Sub cmdProximo_Click()
    If mPaginaAtual < mTotalPaginas Then
        mPaginaAtual = mPaginaAtual + 1
        PopularListBox
    End If
End Sub

' ====================================================================
' SOMAS TOTAIS
' ====================================================================

Private Sub AtualizarSomas()
    Dim totalFat As Double, totalGlosa As Double, totalPerda As Double
    Dim i As Long

    For i = 1 To mTotalFiltrados
        totalFat = totalFat + val(mFiltrados(i, 9))
        totalGlosa = totalGlosa + val(mFiltrados(i, 10))
        totalPerda = totalPerda + val(mFiltrados(i, 11))
    Next

    lblFaturamento.Caption = Format(totalFat, "R$ #,##0.00")
    lblGlosa.Caption = Format(totalGlosa, "R$ #,##0.00")
    lblPerda.Caption = Format(totalPerda, "R$ #,##0.00")
End Sub

' ====================================================================
' BOTOES (placeholders)
' ====================================================================

Private Sub cmdAdicionar_Click()
    MsgBox "Funcionalidade em desenvolvimento.", vbInformation, "Adicionar"
End Sub

Private Sub cmbEditar_Click()
    If lstDados.ListIndex < 0 Then
        MsgBox "Selecione um registro para editar.", vbExclamation, "Editar"
        Exit Sub
    End If
    MsgBox "Funcionalidade em desenvolvimento.", vbInformation, "Editar"
End Sub

Private Sub cmbExcluir_Click()
    If lstDados.ListIndex < 0 Then
        MsgBox "Selecione um registro para excluir.", vbExclamation, "Excluir"
        Exit Sub
    End If
    If MsgBox("Deseja realmente excluir este registro?", vbQuestion + vbYesNo, "Excluir") = vbNo Then Exit Sub
    MsgBox "Funcionalidade em desenvolvimento.", vbInformation, "Excluir"
End Sub




