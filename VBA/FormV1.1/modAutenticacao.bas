Attribute VB_Name = "modAutenticacao"
Option Explicit

' === Variaveis de sessao ===
Public UsuarioAtual As Long
Public EmailAtual As String

' === Variaveis internas ===
Private mCaminhoBanco As String
Private mBancoAberto As Workbook

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
' ACESSO AO BANCO
' ====================================================================

Public Function AbrirBanco(ByVal readOnly As Boolean) As Workbook
    Dim caminho As String
    caminho = ObterCaminhoBanco
    If caminho = "" Then
        Dim msg As String
        msg = "Banco de dados nao encontrado." & vbCrLf & vbCrLf
        msg = msg & "Verifique o caminho na planilha Config (celula A1)." & vbCrLf
        msg = msg & "Deseja informar o caminho agora?"
        If MsgBox(msg, vbCritical + vbYesNo, "Erro") = vbYes Then
            mCaminhoBanco = ""
            caminho = SolicitarCaminhoBanco
            If caminho <> "" Then
                Set AbrirBanco = AbrirBancoComErro(caminho, readOnly)
            End If
        End If
        Exit Function
    End If
    
    Set AbrirBanco = AbrirBancoComErro(caminho, readOnly)
End Function

Private Function AbrirBancoComErro(ByVal caminho As String, ByVal readOnly As Boolean) As Workbook
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    
    Dim tempWB As Workbook
    On Error Resume Next
    Set tempWB = Workbooks.Open(caminho, , readOnly)
    On Error GoTo 0
    
    Application.DisplayAlerts = True
    
    If tempWB Is Nothing Then
        Application.ScreenUpdating = True
        Dim errMsg As String
        errMsg = "Nao foi possivel abrir o banco de dados." & vbCrLf & vbCrLf & _
                 "Caminho: " & caminho & vbCrLf & vbCrLf & _
                 "Possiveis causas:" & vbCrLf & _
                 "- O arquivo foi movido ou renomeado" & vbCrLf & _
                 "- O caminho de rede esta inacessivel" & vbCrLf & _
                 "- O arquivo esta corrompido ou em uso" & vbCrLf & vbCrLf & _
                 "Deseja informar um novo caminho?"
        If MsgBox(errMsg, vbCritical + vbYesNo, "Erro") = vbYes Then
            Dim novo As String
            novo = SolicitarCaminhoBanco
            If novo <> "" Then
                Set AbrirBancoComErro = AbrirBancoComErro(novo, readOnly)
            End If
        End If
    Else
        Set AbrirBancoComErro = tempWB
    End If
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

Public Sub FecharBanco(ByVal db As Workbook)
    If Not db Is Nothing Then
        db.Close False
    End If
    Application.ScreenUpdating = True
End Sub

' ====================================================================
' FUNCOES DE AUTENTICACAO
' ====================================================================

Public Function CarregarEmailsAtivos() As String()
    Dim db As Workbook
    Set db = AbrirBanco(True)
    If db Is Nothing Then Exit Function
    
    Dim ws As Worksheet
    Set ws = db.Sheets("Usuarios")
    
    Dim lo As ListObject
    Set lo = ws.ListObjects("TabUsuarios")
    
    If lo Is Nothing Then
        FecharBanco db
        Exit Function
    End If
    
    Dim tb As Range
    Set tb = lo.DataBodyRange
    
    If tb Is Nothing Then
        FecharBanco db
        Exit Function
    End If
    
    Dim i As Long, count As Long
    count = 0
    
    For i = 1 To tb.Rows.count
        If tb.Cells(i, 4).Value = 1 Then
            count = count + 1
        End If
    Next
    
    If count = 0 Then
        FecharBanco db
        Exit Function
    End If
    
    Dim emails() As String
    ReDim emails(1 To count)
    
    Dim idx As Long
    idx = 1
    
    For i = 1 To tb.Rows.count
        If tb.Cells(i, 4).Value = 1 Then
            emails(idx) = tb.Cells(i, 2).Value
            idx = idx + 1
        End If
    Next
    
    FecharBanco db
    CarregarEmailsAtivos = emails
End Function

Public Function VerificarCredenciais(ByVal pEmail As String, ByVal pSenha As String) As Boolean
    Dim db As Workbook
    Set db = AbrirBanco(True)
    If db Is Nothing Then Exit Function
    
    Dim ws As Worksheet
    Set ws = db.Sheets("Usuarios")
    
    Dim lo As ListObject
    Set lo = ws.ListObjects("TabUsuarios")
    
    If lo Is Nothing Then
        FecharBanco db
        Exit Function
    End If
    
    Dim tb As Range
    Set tb = lo.DataBodyRange
    
    If tb Is Nothing Then
        FecharBanco db
        Exit Function
    End If
    
    Dim i As Long
    For i = 1 To tb.Rows.count
        If LCase(Trim(tb.Cells(i, 2).Value)) = LCase(Trim(pEmail)) Then
            If tb.Cells(i, 4).Value = 1 Then
                If tb.Cells(i, 3).Value = pSenha Then
                    VerificarCredenciais = True
                    FecharBanco db
                    Exit Function
                End If
            Else
                FecharBanco db
                MsgBox "Usuario inativo entre em contato com o administrador do sistema", vbExclamation, "Acesso Negado"
                Exit Function
            End If
        End If
    Next
    
    FecharBanco db
    MsgBox "Email ou senha incorretos.", vbExclamation, "Falha no Login"
End Function

Public Function ObterIdUsuario(ByVal pEmail As String) As Long
    Dim db As Workbook
    Set db = AbrirBanco(True)
    If db Is Nothing Then Exit Function
    
    Dim ws As Worksheet
    Set ws = db.Sheets("Usuarios")
    
    Dim lo As ListObject
    Set lo = ws.ListObjects("TabUsuarios")
    
    If lo Is Nothing Then
        FecharBanco db
        Exit Function
    End If
    
    Dim tb As Range
    Set tb = lo.DataBodyRange
    
    If tb Is Nothing Then
        FecharBanco db
        Exit Function
    End If
    
    Dim i As Long
    For i = 1 To tb.Rows.count
        If LCase(Trim(tb.Cells(i, 2).Value)) = LCase(Trim(pEmail)) Then
            ObterIdUsuario = tb.Cells(i, 1).Value
            FecharBanco db
            Exit Function
        End If
    Next
    
    FecharBanco db
End Function

Public Sub ResetarSessao()
    UsuarioAtual = 0
    EmailAtual = ""
End Sub

Public Function ObterCaminhoBancoConfig() As String
    ObterCaminhoBancoConfig = ObterCaminhoBanco
End Function
