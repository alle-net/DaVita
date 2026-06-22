Attribute VB_Name = "modAutenticacao"
Option Explicit

Public UsuarioAtual As Long
Public EmailAtual As String

Private mCaminhoBanco As String

Private Const STR_PROVIDER As String = "Microsoft.ACE.OLEDB.12.0"
Private Const STR_EXTENDED As String = "Excel 12.0 Xml;HDR=Yes;IMEX=1"

' ====================================================================
' GERENCIAMENTO DO CAMINHO DO BANCO
' ====================================================================

Private Function ObterCaminhoBanco() As String
    If mCaminhoBanco <> "" Then
        ObterCaminhoBanco = mCaminhoBanco
        Exit Function
    End If

    Dim configPath As String
    configPath = LerConfig
    If configPath <> "" Then
        If Dir(configPath) <> "" Then
            mCaminhoBanco = configPath
        End If
    End If

    ObterCaminhoBanco = mCaminhoBanco
End Function

' ====================================================================
' CONFIG SHEET
' ====================================================================

Private Function LerConfig() As String
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Config")
    If Not ws Is Nothing Then
        LerConfig = ws.Range("A1").Value
    End If
    On Error GoTo 0
End Function

Private Sub SalvarConfig(ByVal caminho As String)
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Config")
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Sheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.count))
        ws.Name = "Config"
        ws.Visible = xlSheetVeryHidden
    End If
    On Error GoTo 0
    ws.Range("A1").Value = caminho
End Sub

' ====================================================================
' CONEXAO ADODB
' ====================================================================

Public Function AbrirConexao() As Object
    Dim caminho As String

    caminho = ObterCaminhoBanco
    If caminho = "" Then Exit Function
    If Dir(caminho) = "" Then Exit Function

    Dim conn As Object
    Set conn = CreateObject("ADODB.Connection")

    On Error Resume Next
    conn.Open "Provider=" & STR_PROVIDER & ";Data Source=" & caminho & _
              ";Extended Properties=""" & STR_EXTENDED & """"
    On Error GoTo 0

    If conn.State <> 1 Then
        Set conn = Nothing
        Exit Function
    End If

    Set AbrirConexao = conn
End Function

Public Sub FecharConexao(ByVal conn As Object)
    On Error Resume Next
    If Not conn Is Nothing Then
        If conn.State = 1 Then conn.Close
    End If
    Set conn = Nothing
    On Error GoTo 0
End Sub

Public Function ExecutarSelect(ByVal conn As Object, ByVal sql As String) As Object
    If conn Is Nothing Then Exit Function

    Dim rs As Object
    Set rs = CreateObject("ADODB.Recordset")

    On Error Resume Next
    rs.Open sql, conn, 0, 1
    On Error GoTo 0

    If rs.State <> 1 Then
        Set rs = Nothing
    End If

    Set ExecutarSelect = rs
End Function

Public Function AbrirDialogoSelecaoBanco() As Boolean
    Dim fdlg As Object
    Set fdlg = Application.FileDialog(1)

    With fdlg
        .Title = "Selecione o arquivo Banco Analistas.xlsx"
        .AllowMultiSelect = False
        .Filters.Clear
        .Filters.Add "Arquivos Excel", "*.xlsx"
        .Filters.Add "Todos os arquivos", "*.*"

        Dim user As String
        user = Environ("USERNAME")
        Dim pastaInicial As String
        pastaInicial = "C:\Users\" & user & "\DaVita\"
        On Error Resume Next
        If Dir(pastaInicial, vbDirectory) <> "" Then
            .InitialFileName = pastaInicial
        End If
        On Error GoTo 0

        If .Show = -1 Then
            Dim caminho As String
            caminho = .SelectedItems(1)
            If Dir(caminho) <> "" Then
                mCaminhoBanco = caminho
                SalvarConfig caminho
                AbrirDialogoSelecaoBanco = True
            End If
        End If
    End With
    Set fdlg = Nothing
End Function

' ====================================================================
' AUTENTICACAO
' ====================================================================

Public Function CarregarEmailsAtivos() As String()
    Dim conn As Object
    Set conn = AbrirConexao
    If conn Is Nothing Then Exit Function

    Dim rs As Object
    Set rs = ExecutarSelect(conn, "SELECT Email FROM [Usuarios$] WHERE Status = 1")
    If rs Is Nothing Then
        FecharConexao conn
        Exit Function
    End If

    If rs.EOF Then
        rs.Close
        FecharConexao conn
        Exit Function
    End If

    Dim emails() As String
    ReDim emails(1 To 1000)

    Dim idx As Long
    idx = 0
    Do While Not rs.EOF
        idx = idx + 1
        If idx > UBound(emails) Then ReDim Preserve emails(1 To idx + 1000)
        emails(idx) = rs.Fields("Email").Value
        rs.MoveNext
    Loop

    rs.Close
    FecharConexao conn

    If idx = 0 Then Exit Function
    ReDim Preserve emails(1 To idx)
    CarregarEmailsAtivos = emails
End Function

Public Function VerificarCredenciais(ByVal pEmail As String, ByVal pSenha As String) As Boolean
    Dim conn As Object
    Set conn = AbrirConexao
    If conn Is Nothing Then
        MsgBox "Banco de dados nao configurado. Clique em 'Configurar Banco' para localizar o arquivo Banco Analistas.xlsx.", _
               vbExclamation, "Banco nao encontrado"
        Exit Function
    End If

    pEmail = Replace(pEmail, "'", "''")
    pSenha = Replace(pSenha, "'", "''")

    Dim sql As String
    sql = "SELECT IdUsuario, Senha, Status FROM [Usuarios$] WHERE UCASE(Email) = UCASE('" & pEmail & "')"

    Dim rs As Object
    Set rs = ExecutarSelect(conn, sql)
    If rs Is Nothing Then
        FecharConexao conn
        Exit Function
    End If

    If Not rs.EOF Then
        If rs.Fields("Status").Value = 1 Then
            If rs.Fields("Senha").Value = pSenha Then
                VerificarCredenciais = True
            End If
        Else
            FecharConexao conn
            MsgBox "Usuario inativo entre em contato com o administrador do sistema", vbExclamation, "Acesso Negado"
            Exit Function
        End If
    End If

    rs.Close
    FecharConexao conn

    If Not VerificarCredenciais Then
        MsgBox "Email ou senha incorretos.", vbExclamation, "Falha no Login"
    End If
End Function

Public Function ObterIdUsuario(ByVal pEmail As String) As Long
    Dim conn As Object
    Set conn = AbrirConexao
    If conn Is Nothing Then Exit Function

    pEmail = Replace(pEmail, "'", "''")

    Dim sql As String
    sql = "SELECT IdUsuario FROM [Usuarios$] WHERE UCASE(Email) = UCASE('" & pEmail & "')"

    Dim rs As Object
    Set rs = ExecutarSelect(conn, sql)
    If rs Is Nothing Then
        FecharConexao conn
        Exit Function
    End If

    If Not rs.EOF Then
        ObterIdUsuario = rs.Fields("IdUsuario").Value
    End If

    rs.Close
    FecharConexao conn
End Function

Public Sub ResetarSessao()
    UsuarioAtual = 0
    EmailAtual = ""
End Sub

Public Function ObterCaminhoBancoConfig() As String
    ObterCaminhoBancoConfig = ObterCaminhoBanco
End Function
