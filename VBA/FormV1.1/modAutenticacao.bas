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
            ObterCaminhoBanco = mCaminhoBanco
            Exit Function
        Else
            Dim msg As String
            msg = "O caminho salvo nao foi encontrado:" & vbCrLf & vbCrLf & _
                  configPath & vbCrLf & vbCrLf & _
                  "Deseja informar um novo caminho?"
            If MsgBox(msg, vbQuestion + vbYesNo, "Arquivo nao encontrado") = vbNo Then
                Exit Function
            End If
        End If
    End If

    Dim user As String
    user = Environ("USERNAME")

    mCaminhoBanco = ProcurarBancoEm("C:\Users\" & user & "\DaVita\")

    If mCaminhoBanco <> "" Then
        SalvarConfig mCaminhoBanco
        ObterCaminhoBanco = mCaminhoBanco
        Exit Function
    End If

    Dim resposta As String
    resposta = InputBox("Informe o caminho completo do arquivo Banco Analistas.xlsx:" & vbCrLf & _
                        "Ex: C:\Users\" & user & "\DaVita\...\Banco Analistas.xlsx", _
                        "Configuracao do Banco")
    If resposta <> "" And Dir(resposta) <> "" Then
        mCaminhoBanco = resposta
        SalvarConfig mCaminhoBanco
    ElseIf resposta <> "" Then
        mCaminhoBanco = resposta
    End If

    ObterCaminhoBanco = mCaminhoBanco
End Function

Private Function ProcurarBancoEm(ByVal pastaBase As String) As String
    Dim fso As Object
    Set fso = CreateObject("Scripting.FileSystemObject")

    If Not fso.FolderExists(pastaBase) Then Exit Function

    Dim pasta As Object
    Set pasta = fso.GetFolder(pastaBase)
    ProcurarBancoEm = BuscarRecursivo(pasta, "Banco Analistas.xlsx", 3)
End Function

Private Function BuscarRecursivo(ByVal pasta As Object, ByVal nomeArquivo As String, ByVal profundidade As Long) As String
    Dim arq As Object, subPasta As Object

    For Each arq In pasta.Files
        If LCase(arq.Name) = LCase(nomeArquivo) Then
            BuscarRecursivo = arq.Path
            Exit Function
        End If
    Next

    If profundidade > 0 Then
        For Each subPasta In pasta.SubFolders
            BuscarRecursivo = BuscarRecursivo(subPasta, nomeArquivo, profundidade - 1)
            If BuscarRecursivo <> "" Then Exit Function
        Next
    End If
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

    If Dir(caminho) = "" Then
        Dim errMsg As String
        errMsg = "Arquivo nao encontrado:" & vbCrLf & vbCrLf & _
                 caminho & vbCrLf & vbCrLf & _
                 "Deseja informar um novo caminho?"
        If MsgBox(errMsg, vbCritical + vbYesNo, "Arquivo nao encontrado") = vbYes Then
            mCaminhoBanco = ""
            caminho = SolicitarCaminhoBanco
            If caminho <> "" Then
                Set AbrirConexao = AbrirConexao
            End If
        End If
        Exit Function
    End If

    Dim conn As Object
    Set conn = CreateObject("ADODB.Connection")

    On Error Resume Next
    conn.Open "Provider=" & STR_PROVIDER & ";Data Source=" & caminho & _
              ";Extended Properties=""" & STR_EXTENDED & """"
    On Error GoTo 0

    If conn.State <> 1 Then
        Set conn = Nothing
        errMsg = "Nao foi possivel conectar ao banco de dados." & vbCrLf & vbCrLf & _
                 "Caminho: " & caminho & vbCrLf & vbCrLf & _
                 "Deseja informar um novo caminho?"
        If MsgBox(errMsg, vbCritical + vbYesNo, "Erro de conexao") = vbYes Then
            mCaminhoBanco = ""
            caminho = SolicitarCaminhoBanco
            If caminho <> "" Then
                Set AbrirConexao = AbrirConexao
            End If
        End If
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

Private Function SolicitarCaminhoBanco() As String
    Dim user As String
    user = Environ("USERNAME")
    Dim resposta As String
    resposta = InputBox("Informe o caminho completo do arquivo Banco Analistas.xlsx:" & vbCrLf & _
                        "Ex: C:\Users\" & user & "\DaVita\...\Banco Analistas.xlsx", _
                        "Configuracao do Banco")
    If resposta <> "" Then
        If Dir(resposta) <> "" Then
            mCaminhoBanco = resposta
            SalvarConfig resposta
            SolicitarCaminhoBanco = resposta
        Else
            Dim confirma As String
            confirma = "O arquivo informado nao foi encontrado:" & vbCrLf & _
                       resposta & vbCrLf & vbCrLf & _
                       "Deseja tentar novamente com outro caminho?"
            If MsgBox(confirma, vbExclamation + vbYesNo, "Arquivo nao encontrado") = vbYes Then
                SolicitarCaminhoBanco = SolicitarCaminhoBanco
            End If
        End If
    End If
End Function

' ====================================================================
' AUTENTICACAO
' ====================================================================

Public Function CarregarEmailsAtivos() As String()
    Dim conn As Object
    Set conn = AbrirConexao
    If conn Is Nothing Then Exit Function

    Dim rs As Object
    Set rs = ExecutarSelect(conn, "SELECT Email FROM TabUsuarios WHERE Status = 1")
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
    If conn Is Nothing Then Exit Function

    pEmail = Replace(pEmail, "'", "''")
    pSenha = Replace(pSenha, "'", "''")

    Dim sql As String
    sql = "SELECT IdUsuario, Senha, Status FROM TabUsuarios WHERE LCase(Email) = LCase('" & pEmail & "')"

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
    sql = "SELECT IdUsuario FROM TabUsuarios WHERE LCase(Email) = LCase('" & pEmail & "')"

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
