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

Public Function ListarDados() As Variant
    Dim conn As Object
    Set conn = AbrirConexao
    If conn Is Nothing Then Exit Function
    Dim sql As String
    sql = "SELECT IdUsuario, Competencia, IdHospital, IdRegional, IdUnidade, " & _
          "Titulo, NFe, IdStatus, IdMotivo, DataEnvioNFe, " & _
          "ValorFaturamento, ValorPerda, ValorGlosa, Observacao " & _
          "FROM [Dados$] WHERE IdUsuario = " & UsuarioAtual
    Dim rs As Object
    Set rs = ExecutarSelect(conn, sql)
    If rs Is Nothing Then
        FecharConexao conn
        Exit Function
    End If
    Dim dados() As Variant
    Dim linha As Long
    Dim total As Long
    linha = 0
    total = 1000
    ReDim dados(1 To total, 1 To 14)
    Do While Not rs.EOF
        linha = linha + 1
        If linha > total Then
            total = total + 1000
            ReDim Preserve dados(1 To total, 1 To 14)
        End If
        dados(linha, 1) = rs.Fields("Competencia").Value
        dados(linha, 2) = rs.Fields("IdHospital").Value
        dados(linha, 3) = rs.Fields("IdRegional").Value
        dados(linha, 4) = rs.Fields("IdUnidade").Value
        dados(linha, 5) = rs.Fields("Titulo").Value
        dados(linha, 6) = rs.Fields("NFe").Value
        dados(linha, 7) = rs.Fields("IdStatus").Value
        dados(linha, 8) = rs.Fields("IdMotivo").Value
        dados(linha, 9) = rs.Fields("DataEnvioNFe").Value
        dados(linha, 10) = rs.Fields("ValorFaturamento").Value
        dados(linha, 11) = rs.Fields("ValorPerda").Value
        dados(linha, 12) = rs.Fields("ValorGlosa").Value
        dados(linha, 13) = rs.Fields("Observacao").Value
        dados(linha, 14) = rs.Fields("IdUsuario").Value
        rs.MoveNext
    Loop
    rs.Close
    FecharConexao conn
    If linha = 0 Then Exit Function
    If linha < total Then
        ReDim Preserve dados(1 To linha, 1 To 14)
    End If
    ListarDados = dados
End Function

Public Function ListarDimensao(ByVal tabela As String, ByVal colId As String, _
                                ByVal colNome As String) As Object
    Dim dict As Object
    Set dict = CreateObject("Scripting.Dictionary")
    Dim conn As Object
    Set conn = AbrirConexao
    If conn Is Nothing Then
        Set ListarDimensao = dict
        Exit Function
    End If
    Dim sql As String
    sql = "SELECT " & colId & ", " & colNome & " FROM [" & tabela & "$] WHERE Status = 1"
    Dim rs As Object
    Set rs = ExecutarSelect(conn, sql)
    If rs Is Nothing Then
        FecharConexao conn
        Set ListarDimensao = dict
        Exit Function
    End If
    Do While Not rs.EOF
        dict(rs.Fields(0).Value) = rs.Fields(1).Value
        rs.MoveNext
    Loop
    rs.Close
    FecharConexao conn
    Set ListarDimensao = dict
End Function

Public Function ListarUsuarios() As Object
    Dim dict As Object
    Set dict = CreateObject("Scripting.Dictionary")
    Dim conn As Object
    Set conn = AbrirConexao
    If conn Is Nothing Then
        Set ListarUsuarios = dict
        Exit Function
    End If
    Dim rs As Object
    Set rs = ExecutarSelect(conn, "SELECT IdUsuario, Email FROM [Usuarios$] WHERE Status = 1")
    If rs Is Nothing Then
        FecharConexao conn
        Set ListarUsuarios = dict
        Exit Function
    End If
    Do While Not rs.EOF
        dict(rs.Fields("IdUsuario").Value) = rs.Fields("Email").Value
        rs.MoveNext
    Loop
    rs.Close
    FecharConexao conn
    Set ListarUsuarios = dict
End Function
