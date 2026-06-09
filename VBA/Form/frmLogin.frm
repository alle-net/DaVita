VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmLogin 
   Caption         =   "Login"
   ClientHeight    =   3630
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   6120
   OleObjectBlob   =   "frmLogin.frx":0000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "frmLogin"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit
Private Sub UserForm_Initialize()
    CarregarEmails
    Me.Left = (Application.Width - Me.Width) / 2
    Me.Top = (Application.Height - Me.Height) / 2
    txtSenha.SetFocus
End Sub
Private Sub CarregarEmails()
    Dim em() As String, i As Long
    em = modAutenticacao.CarregarEmailsAtivos
    cboEmail.Clear
    If (Not em) = -1 Then Exit Sub
    For i = LBound(em) To UBound(em)
        cboEmail.AddItem em(i)
    Next i
    If cboEmail.ListCount > 0 Then cboEmail.ListIndex = 0
End Sub
Private Sub cboEmail_Change()
    lblMensagem = ""
End Sub
Private Sub txtSenha_Change()
    lblMensagem = ""
End Sub
Private Sub cmdEntrar_Click()
    Dim e As String, s As String
    e = Trim(cboEmail.Value)
    s = Trim(txtSenha.Value)
    lblMensagem = ""
    If e = "" Then lblMensagem = "Selecione um e-mail.": cboEmail.SetFocus: Exit Sub
    If s = "" Then lblMensagem = "Digite a senha.": txtSenha.SetFocus: Exit Sub
    If modAutenticacao.VerificarCredenciais(e, s) Then
        modAutenticacao.UsuarioAtual = modAutenticacao.ObterIdUsuario(e)
        modAutenticacao.EmailAtual = e
        txtSenha.Value = ""
        Me.Hide
    Else
        lblMensagem = "E-mail ou senha invalidos."
        txtSenha.Value = ""
        txtSenha.SetFocus
    End If
End Sub
Private Sub cmdCancelar_Click()
    If MsgBox("Deseja cancelar?", vbQuestion + vbYesNo, "Login") = vbYes Then
        modAutenticacao.ResetarSessao
        Unload Me
    End If
End Sub
Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    If CloseMode = 0 Then Cancel = 1: cmdCancelar_Click
End Sub
