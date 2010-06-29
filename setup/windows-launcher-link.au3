; UFO-launcher - A multi-platform virtual machine launcher for the UFO OS
;
; Copyright (c) 2008-2010 Agorabox, Inc.
;
; This is free software; you can redistribute it and/or modify it
; under the terms of the GNU General Public License as published by
; the Free Software Foundation; either version 2 of the License, or
; (at your option) any later version.
;
; This program is distributed in the hope that it will be useful, but
; WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
; General Public License for more details.
;
; You should have received a copy of the GNU General Public License
; along with this program; if not, write to the Free Software
; Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

#RequireAdmin

Dim $bindir, $arch

If EnvGet("PROCESSOR_ARCHITEW6432") Then
    $bindir = "bin64"
    $arch = "AMD64"
Else
    $bindir = "bin"
    $arch = "x86"
EndIf

Run(@ScriptDir & "\" & $bindir & "\" & "ufo." & $arch & ".exe", @ScriptDir & "\" & $bindir)
