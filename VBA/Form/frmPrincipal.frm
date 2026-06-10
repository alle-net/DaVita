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
Option Explicit

Private Sub UserForm_Initialize()
    lblUsuarioLogado.Caption = "Usuario: " & modAutenticacao.EmailAtual
    lblFaturamento.ForeColor = RGB(0, 118, 182)
    lblFaturamento.Font.Bold = True
    lblGlosa.ForeColor = RGB(0, 118, 182)
    lblGlosa.Font.Bold = True
    lblPerda.ForeColor = RGB(0, 118, 182)
    lblPerda.Font.Bold = True
    
    If modDados.CarregarDadosUsuario(modAutenticacao.UsuarioAtual) Then
        PreencherGrid
        AtualizarNavegacao
        AtualizarSubtotais
    End If
    AtualizarBotoesAcao
End Sub

Private Sub PreencherGrid()
    Dim dados As Variant
    dados = modDados.GetPageDataFormatado
    
    With lstDados
        .Clear
        If Not IsArray(dados) Then Exit Sub
        If UBound(dados, 1) < 0 Then Exit Sub
        .ColumnCount = 13
        .ColumnWidths = "44;70;70;200;70;70;100;44;70;70;70;70;70"
        .List = dados
    End With
    AtualizarBotoesAcao
End Sub

Private Sub AtualizarNavegacao()
    lblPagina.Caption = modDados.GetPageInfo
    cmdAnterior.Enabled = (modDados.GetCurrentPage > 1)
    cmdProximo.Enabled = (modDados.GetCurrentPage < modDados.GetTotalPages)
End Sub

Private Sub AtualizarSubtotais()
    Dim fat As Double, perda As Double, glosa As Double
    modDados.CalcularSubtotais fat, perda, glosa
    lblFaturamento.Caption = "R$ " & Format$(fat, "#,##0.00")
    lblGlosa.Caption = "R$ " & Format$(glosa, "#,##0.00")
    lblPerda.Caption = "R$ " & Format$(perda, "#,##0.00")
End Sub

Private Sub txtBoxFiltro_Change()
    modDados.AplicarFiltro txtBoxFiltro.Value
    PreencherGrid
    AtualizarNavegacao
    AtualizarSubtotais
End Sub

Private Sub cmdAnterior_Click()
    modDados.PreviousPage
    PreencherGrid
    AtualizarNavegacao
End Sub

Private Sub cmdProximo_Click()
    modDados.NextPage
    PreencherGrid
    AtualizarNavegacao
End Sub

Private Sub lstDados_Click()
    AtualizarBotoesAcao
End Sub

Private Sub AtualizarBotoesAcao()
    Dim selecionou As Boolean
    selecionou = (lstDados.ListIndex >= 0)
    cmdEditar.Enabled = selecionou
    cmdExcluir.Enabled = selecionou
End Sub

Private Sub cmdAdd_Click()
    Dim frm As frmRegistro
    Set frm = New frmRegistro
    frm.Mostrar False
    If modDados.CarregarDadosUsuario(modAutenticacao.UsuarioAtual) Then
        txtBoxFiltro.Value = ""
        PreencherGrid
        AtualizarNavegacao
        AtualizarSubtotais
    End If
End Sub

Private Sub cmdEditar_Click()
    If lstDados.ListIndex = -1 Then
        MsgBox "Selecione um registro.", vbExclamation, "Editar"
        Exit Sub
    End If
    Dim rawPage As Variant, GUID As String
    rawPage = modDados.GetPageData
    If Not IsArray(rawPage) Then Exit Sub
    GUID = rawPage(lstDados.ListIndex, 0)
    Dim frm As frmRegistro
    Set frm = New frmRegistro
    frm.Mostrar True, GUID
    If modDados.CarregarDadosUsuario(modAutenticacao.UsuarioAtual) Then
        PreencherGrid
        AtualizarNavegacao
        AtualizarSubtotais
    End If
End Sub

Private Sub cmdExcluir_Click()
    If lstDados.ListIndex = -1 Then
        MsgBox "Selecione um registro.", vbExclamation, "Excluir"
        Exit Sub
    End If
    Dim rawPage As Variant, GUID As String
    rawPage = modDados.GetPageData
    If Not IsArray(rawPage) Then Exit Sub
    GUID = rawPage(lstDados.ListIndex, 0)
    If MsgBox("Deseja excluir este registro?", vbQuestion + vbYesNo, "Excluir") = vbYes Then
        If modDados.ExcluirRegistro(GUID) Then
            ThisWorkbook.Save
            If modDados.CarregarDadosUsuario(modAutenticacao.UsuarioAtual) Then
                txtBoxFiltro.Value = ""
                PreencherGrid
                AtualizarNavegacao
                AtualizarSubtotais
            End If
        Else
            MsgBox "Erro ao excluir registro.", vbCritical, "Erro"
        End If
    End If
End Sub

Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    If CloseMode = 0 Then
        modAutenticacao.ResetarSessao
    End If
End Sub

Private Sub UserForm_Terminate()
    ThisWorkbook.Close SaveChanges:=True
End Sub

