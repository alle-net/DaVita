Attribute VB_Name = "modDados"
Option Explicit

Public Const PAGE_SIZE As Long = 25

Private mAllData() As Variant
Private mFilteredIdx() As Long
Private mTotalRecords As Long
Private mTotalFiltered As Long
Private mCurrentPage As Long
Private mTotalPages As Long

Public Function CarregarDadosUsuario(usuarioID As Long) As Boolean
    Dim ws As Worksheet, tb As ListObject, dr As Range
    Dim i As Long, n As Long
    
    On Error GoTo ErrHandler
    Set ws = ThisWorkbook.Worksheets("Dados")
    Set tb = ws.ListObjects("TabDados")
    
    If tb.DataBodyRange Is Nothing Then
        mTotalRecords = 0: mTotalFiltered = 0
        mCurrentPage = 1: mTotalPages = 1
        ReDim mAllData(1 To 1, 1 To 16)
        CarregarDadosUsuario = True: Exit Function
    End If
    
    Dim rawData As Variant
    rawData = tb.DataBodyRange.Value
    n = 0
    For i = 1 To UBound(rawData, 1)
        If rawData(i, 2) = usuarioID Then n = n + 1
    Next i
    
    If n = 0 Then
        mTotalRecords = 0: mTotalFiltered = 0
        mCurrentPage = 1: mTotalPages = 1
        ReDim mAllData(1 To 1, 1 To 16)
        CarregarDadosUsuario = True: Exit Function
    End If
    
    ReDim mAllData(1 To n, 1 To 16): n = 0
    For i = 1 To UBound(rawData, 1)
        If rawData(i, 2) = usuarioID Then
            n = n + 1
            Dim c As Long
            For c = 1 To 16
                mAllData(n, c) = ValorSeguro(rawData(i, c))
            Next c
        End If
    Next i
    
    mTotalRecords = n
    ReDim mFilteredIdx(1 To n)
    For i = 1 To n: mFilteredIdx(i) = i: Next i
    mTotalFiltered = n
    
    mCurrentPage = 1
    mTotalPages = ((n - 1) \ PAGE_SIZE) + 1
    CarregarDadosUsuario = True: Exit Function
ErrHandler:
    CarregarDadosUsuario = False
End Function

Public Sub AplicarFiltro(texto As String)
    Dim i As Long, j As Long, n As Long, txt As String
    txt = LCase(Trim(texto))
    
    If txt = "" Then
        ReDim mFilteredIdx(1 To mTotalRecords)
        For i = 1 To mTotalRecords: mFilteredIdx(i) = i: Next i
        mTotalFiltered = mTotalRecords
    Else
        n = 0
        For i = 1 To mTotalRecords
            For j = 1 To 16
                If InStr(LCase(CStr(mAllData(i, j))), txt) > 0 Then
                    n = n + 1
                    mFilteredIdx(n) = i
                    Exit For
                End If
            Next j
        Next i
        If n = 0 Then
            mTotalFiltered = 0: ReDim mFilteredIdx(1 To 1)
        Else
            ReDim Preserve mFilteredIdx(1 To n)
            mTotalFiltered = n
        End If
    End If
    
    mCurrentPage = 1
    If mTotalFiltered = 0 Then mTotalPages = 1 Else mTotalPages = ((mTotalFiltered - 1) \ PAGE_SIZE) + 1
End Sub

Public Function GetPageData() As Variant
    Dim si As Long, ei As Long, i As Long, j As Long, n As Long
    Dim r() As Variant, idx As Long
    
    If mTotalFiltered = 0 Then
        GetPageData = Array(): Exit Function
    End If
    
    si = (mCurrentPage - 1) * PAGE_SIZE + 1
    ei = si + PAGE_SIZE - 1
    If ei > mTotalFiltered Then ei = mTotalFiltered
    
    n = ei - si + 1: ReDim r(0 To n - 1, 0 To 15)
    For i = si To ei
        idx = mFilteredIdx(i): j = i - si
        Dim c2 As Long
        For c2 = 1 To 16
            r(j, c2 - 1) = mAllData(idx, c2)
        Next c2
    Next i
    GetPageData = r
End Function

Public Function GetPageInfo() As String
    If mTotalFiltered = 0 Then
        GetPageInfo = "Pagina 0 de 0 (0 registros)"
    Else
        GetPageInfo = "Pagina " & mCurrentPage & " de " & mTotalPages & _
                      " (" & mTotalFiltered & " registros)"
    End If
End Function

Public Sub GoToPage(p As Long)
    If p >= 1 And p <= mTotalPages Then mCurrentPage = p
End Sub

Public Sub NextPage()
    If mCurrentPage < mTotalPages Then mCurrentPage = mCurrentPage + 1
End Sub

Public Sub PreviousPage()
    If mCurrentPage > 1 Then mCurrentPage = mCurrentPage - 1
End Sub

Public Function GetCurrentPage() As Long: GetCurrentPage = mCurrentPage: End Function
Public Function GetTotalPages() As Long: GetTotalPages = mTotalPages: End Function
Public Function GetTotalFiltered() As Long: GetTotalFiltered = mTotalFiltered: End Function

Public Sub CalcularSubtotais(ByRef pFat As Double, ByRef pPerda As Double, ByRef pGlosa As Double)
    Dim i As Long, idx As Long
    pFat = 0: pPerda = 0: pGlosa = 0
    For i = 1 To mTotalFiltered
        idx = mFilteredIdx(i)
        If IsNumeric(mAllData(idx, 12)) Then pFat = pFat + CDbl(mAllData(idx, 12))
        If IsNumeric(mAllData(idx, 13)) Then pPerda = pPerda + CDbl(mAllData(idx, 13))
        If IsNumeric(mAllData(idx, 14)) Then pGlosa = pGlosa + CDbl(mAllData(idx, 14))
    Next i
End Sub

Private Function ValorSeguro(v As Variant) As Variant
    If IsError(v) Then ValorSeguro = "" Else ValorSeguro = v
End Function
