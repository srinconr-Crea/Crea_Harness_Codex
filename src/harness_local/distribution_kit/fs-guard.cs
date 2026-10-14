// Local-Harness: read-only Windows handles, with no reparse or rename window.
using System;
using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace LocalHarness {
    public static class FileGuard {
        [StructLayout(LayoutKind.Sequential)]
        public struct Info {
            public uint Attributes, CreationLow, CreationHigh, AccessLow, AccessHigh,
                WriteLow, WriteHigh, Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow;
        }
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
        static extern SafeFileHandle CreateFileW(string path, uint access, uint share,
            IntPtr security, uint creation, uint flags, IntPtr template);
        [DllImport("kernel32.dll", SetLastError=true)]
        static extern bool GetFileInformationByHandle(SafeFileHandle handle, out Info info);
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
        static extern uint GetFinalPathNameByHandleW(SafeFileHandle handle, StringBuilder text, uint size, uint flags);
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
        static extern bool CreateDirectoryW(string path, IntPtr security);

        public static void CreateDirectory(string path) {
            if (!CreateDirectoryW(path,IntPtr.Zero)) throw new Win32Exception();
        }

        public static void Validate(SafeFileHandle handle, string expected, bool allowHardlinks) {
            Info info;
            if (!GetFileInformationByHandle(handle,out info) || (info.Attributes & 0x400)!=0 || (!allowHardlinks && info.Links>1))
                throw new IOException("Linked resource rejected");
            var text=new StringBuilder(32768);
            uint length=GetFinalPathNameByHandleW(handle,text,32768,0);
            if (length==0 || length>=32768 || !text.ToString().StartsWith(@"\\?\"))
                throw new IOException("Path unavailable");
            string actual=text.ToString().Substring(4);
            string wanted=Path.GetFullPath(expected);
            // The drive letter has no alternate filesystem identity.
            actual=char.ToUpperInvariant(actual[0])+actual.Substring(1);
            wanted=char.ToUpperInvariant(wanted[0])+wanted.Substring(1);
            if (!String.Equals(actual,wanted,StringComparison.Ordinal))
                throw new IOException("Path alias rejected");
        }

        public static SafeFileHandle PinDirectory(string path) {
            var handle=CreateFileW(path,0x100081,3,IntPtr.Zero,3,0x02200000,IntPtr.Zero);
            if (handle.IsInvalid) { handle.Dispose(); throw new Win32Exception(); }
            try { Validate(handle,path,true); return handle; }
            catch { handle.Dispose(); throw; }
        }

        public static string Identity(SafeFileHandle handle) {
            Info info;
            if (!GetFileInformationByHandle(handle,out info)) throw new IOException("Identity unavailable");
            return info.Volume+":"+info.IndexHigh+":"+info.IndexLow+":"+info.CreationHigh+":"+info.CreationLow;
        }
    }
}
