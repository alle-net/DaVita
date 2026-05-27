VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmLogin
   Caption         =   "Login - Controle Financeiro SH"
   ClientHeight    =   3150
   ClientLeft      =   60
   ClientTop       =   345
   ClientWidth     =   3900
   StartUpPosition =   0  
End
Begin MSForms.ComboBox cboEmail
   Height          =   315
   Left            =   180
   Style           =   2
   TabIndex        =   0
   Top             =   450
   Width           =   3450
End
Begin MSForms.TextBox txtSenha
   Height          =   315
   Left            =   180
   PasswordChar    =   "*"
   TabIndex        =   1
   Top             =   1170
   Width           =   3450
End
Begin MSForms.CommandButton cmdLogin
   Caption         =   "&Entrar"
   Default         =   -1
   Height          =   375
   Left            =   2220
   TabIndex        =   2
   Top             =   1740
   Width           =   1350
End
Begin MSForms.CommandButton cmdCancel
   Caption         =   "&Cancelar"
   Cancel          =   -1
   Height          =   375
   Left            =   750
   TabIndex        =   3
   Top             =   1740
   Width           =   1350
End
Begin MSForms.Label lblEmail
   Caption         =   "Email:"
   Height          =   225
   Left            =   180
   TabIndex        =   4
   Top             =   180
   Width           =   3450
End
Begin MSForms.Label lblSenha
   Caption         =   "Senha:"
   Height          =   225
   Left            =   180
   TabIndex        =   5
   Top             =   900
   Width           =   3450
End
Begin MSForms.Label lblMensagem
   ForeColor       =   255
   Height          =   450
   Left            =   180
   TabIndex        =   6
   Top             =   2340
   Width           =   3450
   WordWrap        =   -1
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

Private Sub cmdLogin_Click()
    Dim e As String, s As String
    e = Trim(cboEmail.Value)
    s = Trim(txtSenha.Value)
    lblMensagem = ""
    If e = "" Then lblMensagem = "Selecione um email.": cboEmail.SetFocus: Exit Sub
    If s = "" Then lblMensagem = "Digite a senha.": txtSenha.SetFocus: Exit Sub
    If modAutenticacao.VerificarCredenciais(e, s) Then
        modAutenticacao.UsuarioAtual = modAutenticacao.ObterIdUsuario(e)
        modAutenticacao.EmailAtual = e
        Me.Hide
        MsgBox "Login realizado! Usuario: " & e & " (ID: " & modAutenticacao.UsuarioAtual & ")", vbInformation, "Controle Financeiro SH"
        Unload Me
    Else
        lblMensagem = "Email ou senha invalidos."
        txtSenha.Value = ""
        txtSenha.SetFocus
    End If
End Sub

Private Sub cmdCancel_Click()
    If MsgBox("Deseja cancelar?", vbQuestion + vbYesNo, "Login") = vbYes Then
        modAutenticacao.ResetarSessao
        Unload Me
    End If
End Sub

Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    If CloseMode = 0 Then Cancel = 1: cmdCancel_Click
End Sub
