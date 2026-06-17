VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmLogin 
   Caption         =   "Login"
   ClientHeight    =   3465
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   5610
   OleObjectBlob   =   "frmLogin.frx":0000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "frmLogin"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
' ============================================================
' frmLogin - Code-Behind
' Cole este codigo no VBA Editor:
'   ALT+F11 -> frmLogin (doublo clique) -> colar tudo
' ============================================================

Option Explicit

Private Sub UserForm_Initialize()
    Me.Caption = "Login - Controle Financeiro"
    
    ' Limpar campos
    cmbEmail.Value = ""
    cmbSenha.Value = ""
    lblMensagem.Caption = ""
    cmbSenha.PasswordChar = "*"
    
    ' Centralizar na tela
    Me.StartUpPosition = 0
    Me.Left = (Application.Width - Me.Width) / 2
    Me.Top = (Application.Height - Me.Height) / 2
    
    ' Foco no campo de email
    cmbEmail.SetFocus
End Sub

Private Sub cmbEntrar_Click()
    Dim email As String
    Dim senha As String
    
    email = Trim(cmbEmail.Value)
    senha = cmbSenha.Value
    
    ' Validar campos
    If email = "" Then
        lblMensagem.Caption = "Informe o email."
        cmbEmail.SetFocus
        Exit Sub
    End If
    
    If senha = "" Then
        lblMensagem.Caption = "Informe a senha."
        cmbSenha.SetFocus
        Exit Sub
    End If
    
    ' Desabilitar botoes durante validacao
    cmbEntrar.Enabled = False
    cmbCancelar.Enabled = False
    lblMensagem.Caption = "Autenticando..."
    DoEvents
    
    ' Verificar credenciais
    If modAutenticacao.VerificarCredenciais(email, senha) Then
        ' Login OK
        modAutenticacao.EmailAtual = email
        modAutenticacao.UsuarioAtual = modAutenticacao.ObterIdUsuario(email)
        Unload Me
    Else
        ' Login falhou
        lblMensagem.Caption = "Email ou senha incorretos."
        cmbSenha.Value = ""
        cmbSenha.SetFocus
        cmbEntrar.Enabled = True
        cmbCancelar.Enabled = True
    End If
End Sub

Private Sub cmbCancelar_Click()
    If MsgBox("Deseja realmente sair?", vbQuestion + vbYesNo, "Sair") = vbYes Then
        modAutenticacao.ResetarSessao
        ThisWorkbook.Close False
    End If
End Sub

Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    ' Fechar com X redireciona para o botao Cancelar
    If CloseMode = 0 Then
        Cancel = True
        cmbCancelar_Click
    End If
End Sub

