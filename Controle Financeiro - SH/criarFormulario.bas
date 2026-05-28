Attribute VB_Name = "CriarFormulario"
Option Explicit

Public Sub CriarFrmLogin()
    On Error GoTo ErrHandler
    
    Dim vba As Object, fc As Object, d As Object, ct As Object
    
    Set vba = Application.VBE.ActiveVBProject
    For Each fc In vba.VBComponents
        If fc.Name = "frmLogin" Then vba.VBComponents.Remove fc: Exit For
    Next
    
    Set fc = vba.VBComponents.Add(3): fc.Name = "frmLogin"
    Set d = fc.Designer
    d.Caption = "Login - Controle Financeiro SH"
    d.Width = 260: d.Height = 210: d.StartUpPosition = 0
    
    Set ct = d.Controls.Add("Forms.Label.1", "lblEmail", True)
    ct.Caption = "Email:": ct.Left = 12: ct.Top = 12: ct.Width = 230: ct.Height = 15
    
    Set ct = d.Controls.Add("Forms.ComboBox.1", "cboEmail", True)
    ct.Left = 12: ct.Top = 30: ct.Width = 230: ct.Height = 21: ct.Style = 2
    
    Set ct = d.Controls.Add("Forms.Label.1", "lblSenha", True)
    ct.Caption = "Senha:": ct.Left = 12: ct.Top = 60: ct.Width = 230: ct.Height = 15
    
    Set ct = d.Controls.Add("Forms.TextBox.1", "txtSenha", True)
    ct.Left = 12: ct.Top = 78: ct.Width = 230: ct.Height = 21: ct.PasswordChar = "*"
    
    Set ct = d.Controls.Add("Forms.CommandButton.1", "cmdLogin", True)
    ct.Caption = "&Entrar": ct.Left = 148: ct.Top = 116: ct.Width = 90: ct.Height = 25: ct.Default = True
    
    Set ct = d.Controls.Add("Forms.CommandButton.1", "cmdCancel", True)
    ct.Caption = "&Cancelar": ct.Left = 50: ct.Top = 116: ct.Width = 90: ct.Height = 25: ct.Cancel = True
    
    Set ct = d.Controls.Add("Forms.Label.1", "lblMensagem", True)
    ct.Left = 12: ct.Top = 156: ct.Width = 230: ct.Height = 30: ct.ForeColor = 255: ct.WordWrap = True
    
    AdicionarCodigoForm fc
    MsgBox "Formulario frmLogin criado com sucesso!", vbInformation, "Sucesso"
    Exit Sub
    
ErrHandler:
    MsgBox "Erro: " & Err.Description, vbCritical, "Erro " & Err.Number
End Sub

Private Sub AdicionarCodigoForm(fc As Object)
    Dim cm As Object: Set cm = fc.CodeModule
    cm.AddFromString "Option Explicit"
    cm.AddFromString "Private Sub UserForm_Initialize()"
    cm.AddFromString "    CarregarEmails"
    cm.AddFromString "    Me.Left = (Application.Width - Me.Width) / 2"
    cm.AddFromString "    Me.Top = (Application.Height - Me.Height) / 2"
    cm.AddFromString "    txtSenha.SetFocus"
    cm.AddFromString "End Sub"
    cm.AddFromString "Private Sub CarregarEmails()"
    cm.AddFromString "    Dim em() As String, i As Long"
    cm.AddFromString "    em = modAutenticacao.CarregarEmailsAtivos"
    cm.AddFromString "    cboEmail.Clear"
    cm.AddFromString "    If (Not em) = -1 Then Exit Sub"
    cm.AddFromString "    For i = LBound(em) To UBound(em): cboEmail.AddItem em(i): Next"
    cm.AddFromString "    If cboEmail.ListCount > 0 Then cboEmail.ListIndex = 0"
    cm.AddFromString "End Sub"
    cm.AddFromString "Private Sub cboEmail_Change(): lblMensagem = "": End Sub"
    cm.AddFromString "Private Sub txtSenha_Change(): lblMensagem = "": End Sub"
    cm.AddFromString "Private Sub cmdLogin_Click()"
    cm.AddFromString "    Dim e As String, s As String"
    cm.AddFromString "    e = Trim(cboEmail.Value): s = Trim(txtSenha.Value)"
    cm.AddFromString "    lblMensagem = """
    cm.AddFromString "    If e = "" Then lblMensagem = ""Selecione um email."": cboEmail.SetFocus: Exit Sub"
    cm.AddFromString "    If s = "" Then lblMensagem = ""Digite a senha."": txtSenha.SetFocus: Exit Sub"
    cm.AddFromString "    If modAutenticacao.VerificarCredenciais(e, s) Then"
    cm.AddFromString "        modAutenticacao.UsuarioAtual = modAutenticacao.ObterIdUsuario(e)"
    cm.AddFromString "        modAutenticacao.EmailAtual = e"
    cm.AddFromString "        Me.Hide"
    cm.AddFromString "        MsgBox ""Login realizado! Usuario: "" & e & "" (ID: "" & modAutenticacao.UsuarioAtual & """", vbInformation, ""Controle Financeiro SH"""
    cm.AddFromString "        Unload Me"
    cm.AddFromString "    Else"
    cm.AddFromString "        lblMensagem = ""Email ou senha invalidos.""
    cm.AddFromString "        txtSenha.Value = """": txtSenha.SetFocus"
    cm.AddFromString "    End If"
    cm.AddFromString "End Sub"
    cm.AddFromString "Private Sub cmdCancel_Click()"
    cm.AddFromString "    If MsgBox(""Deseja cancelar?"", vbQuestion + vbYesNo, ""Login"") = vbYes Then"
    cm.AddFromString "        modAutenticacao.ResetarSessao: Unload Me"
    cm.AddFromString "    End If"
    cm.AddFromString "End Sub"
    cm.AddFromString "Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)"
    cm.AddFromString "    If CloseMode = 0 Then Cancel = 1: cmdCancel_Click"
    cm.AddFromString "End Sub"
End Sub
