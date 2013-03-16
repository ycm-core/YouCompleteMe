//////////////////////////////////////////////////////////////////////////////
//
// (C) Copyright Ion Gaztanaga 2005-2012. Distributed under the Boost
// Software License, Version 1.0. (See accompanying file
// LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//
// See http://www.boost.org/libs/interprocess for documentation.
//
//////////////////////////////////////////////////////////////////////////////

#ifndef BOOST_INTERPROCESS_WIN32_PRIMITIVES_HPP
#define BOOST_INTERPROCESS_WIN32_PRIMITIVES_HPP

#include <boost/interprocess/detail/config_begin.hpp>
#include <boost/interprocess/detail/workaround.hpp>
#include <boost/date_time/filetime_functions.hpp>
#include <cstddef>
#include <cstring>
#include <cassert>
#include <string>
#include <vector>
#include <memory>

#if defined (_MSC_VER) && (_MSC_VER >= 1200)
#  pragma once
#  pragma comment( lib, "advapi32.lib" )
#  pragma comment( lib, "oleaut32.lib" )
#  pragma comment( lib, "Ole32.lib" )
#  pragma comment( lib, "Psapi.lib" )
#endif

#if (defined BOOST_INTERPROCESS_WINDOWS)
#  include <cstdarg>
#  include <boost/detail/interlocked.hpp>
#else
# error "This file can only be included in Windows OS"
#endif


//The structures used in Interprocess with the
//same binary interface as windows ones
namespace boost {
namespace interprocess {
namespace winapi {

//Some used constants
static const unsigned long infinite_time        = 0xFFFFFFFF;
static const unsigned long error_already_exists = 183L;
static const unsigned long error_invalid_handle = 6L;
static const unsigned long error_sharing_violation = 32L;
static const unsigned long error_file_not_found = 2u;
static const unsigned long error_no_more_files  = 18u;
static const unsigned long error_not_locked     = 158L;
//Retries in CreateFile, see http://support.microsoft.com/kb/316609
static const unsigned int  error_sharing_violation_tries = 3u;
static const unsigned int  error_sharing_violation_sleep_ms = 250u;
static const unsigned int  error_file_too_large = 223u;

static const unsigned long semaphore_all_access = (0x000F0000L)|(0x00100000L)|0x3;
static const unsigned long mutex_all_access     = (0x000F0000L)|(0x00100000L)|0x0001;

static const unsigned long page_readonly        = 0x02;
static const unsigned long page_readwrite       = 0x04;
static const unsigned long page_writecopy       = 0x08;
static const unsigned long page_noaccess        = 0x01;

static const unsigned long standard_rights_required   = 0x000F0000L;
static const unsigned long section_query              = 0x0001;
static const unsigned long section_map_write          = 0x0002;
static const unsigned long section_map_read           = 0x0004;
static const unsigned long section_map_execute        = 0x0008;
static const unsigned long section_extend_size        = 0x0010;
static const unsigned long section_all_access         = standard_rights_required |
                                                        section_query            |
                                                        section_map_write        |
                                                        section_map_read         |
                                                        section_map_execute      |
                                                        section_extend_size;

static const unsigned long file_map_copy        = section_query;
static const unsigned long file_map_write       = section_map_write;
static const unsigned long file_map_read        = section_map_read;
static const unsigned long file_map_all_access  = section_all_access;
static const unsigned long delete_access = 0x00010000L;
static const unsigned long file_flag_backup_semantics = 0x02000000;
static const long file_flag_delete_on_close = 0x04000000;

//Native API constants
static const unsigned long file_open_for_backup_intent = 0x00004000;
static const int file_share_valid_flags = 0x00000007;
static const long file_delete_on_close = 0x00001000L;
static const long obj_case_insensitive = 0x00000040L;

static const unsigned long movefile_copy_allowed            = 0x02;
static const unsigned long movefile_delay_until_reboot      = 0x04;
static const unsigned long movefile_replace_existing        = 0x01;
static const unsigned long movefile_write_through           = 0x08;
static const unsigned long movefile_create_hardlink         = 0x10;
static const unsigned long movefile_fail_if_not_trackable   = 0x20;

static const unsigned long file_share_read      = 0x00000001;
static const unsigned long file_share_write     = 0x00000002;
static const unsigned long file_share_delete    = 0x00000004;

static const unsigned long file_attribute_readonly    = 0x00000001;
static const unsigned long file_attribute_hidden      = 0x00000002;
static const unsigned long file_attribute_system      = 0x00000004;
static const unsigned long file_attribute_directory   = 0x00000010;
static const unsigned long file_attribute_archive     = 0x00000020;
static const unsigned long file_attribute_device      = 0x00000040;
static const unsigned long file_attribute_normal      = 0x00000080;
static const unsigned long file_attribute_temporary   = 0x00000100;

static const unsigned long generic_read         = 0x80000000L;
static const unsigned long generic_write        = 0x40000000L;

static const unsigned long wait_object_0        = 0;
static const unsigned long wait_abandoned       = 0x00000080L;
static const unsigned long wait_timeout         = 258L;
static const unsigned long wait_failed          = (unsigned long)0xFFFFFFFF;

static const unsigned long duplicate_close_source  = (unsigned long)0x00000001;
static const unsigned long duplicate_same_access   = (unsigned long)0x00000002;

static const unsigned long format_message_allocate_buffer
   = (unsigned long)0x00000100;
static const unsigned long format_message_ignore_inserts
   = (unsigned long)0x00000200;
static const unsigned long format_message_from_string
   = (unsigned long)0x00000400;
static const unsigned long format_message_from_hmodule
   = (unsigned long)0x00000800;
static const unsigned long format_message_from_system
   = (unsigned long)0x00001000;
static const unsigned long format_message_argument_array
   = (unsigned long)0x00002000;
static const unsigned long format_message_max_width_mask
   = (unsigned long)0x000000FF;
static const unsigned long lang_neutral         = (unsigned long)0x00;
static const unsigned long sublang_default      = (unsigned long)0x01;
static const unsigned long invalid_file_size    = (unsigned long)0xFFFFFFFF;
static const unsigned long invalid_file_attributes =  ((unsigned long)-1);
static       void * const  invalid_handle_value = ((void*)(long)(-1));

static const unsigned long file_type_char    =  0x0002L;
static const unsigned long file_type_disk    =  0x0001L;
static const unsigned long file_type_pipe    =  0x0003L;
static const unsigned long file_type_remote  =  0x8000L;
static const unsigned long file_type_unknown =  0x0000L;

static const unsigned long create_new        = 1;
static const unsigned long create_always     = 2;
static const unsigned long open_existing     = 3;
static const unsigned long open_always       = 4;
static const unsigned long truncate_existing = 5;

static const unsigned long file_begin     = 0;
static const unsigned long file_current   = 1;
static const unsigned long file_end       = 2;

static const unsigned long lockfile_fail_immediately  = 1;
static const unsigned long lockfile_exclusive_lock    = 2;
static const unsigned long error_lock_violation       = 33;
static const unsigned long security_descriptor_revision = 1;

//Own defines
static const long SystemTimeOfDayInfoLength  = 48;
static const long BootAndSystemstampLength   = 16;
static const long BootstampLength            = 8;
static const unsigned long MaxPath           = 260;

//Keys
static void * const  hkey_local_machine = (void*)(unsigned long*)(long)(0x80000002);
static unsigned long key_query_value    = 0x0001;

//COM API
const unsigned long RPC_C_AUTHN_LEVEL_PKT_BIPC = 4;
const unsigned long RPC_C_AUTHN_DEFAULT_BIPC = 0xffffffffL;
const unsigned long RPC_C_AUTHZ_DEFAULT_BIPC = 0xffffffffL;
const unsigned long RPC_C_IMP_LEVEL_IMPERSONATE_BIPC = 3;
const   signed long EOAC_NONE_BIPC = 0;
const   signed long CLSCTX_INPROC_SERVER_BIPC   = 0x1;
const   signed long CLSCTX_LOCAL_SERVER_BIPC   = 0x4;
const   signed long WBEM_FLAG_RETURN_IMMEDIATELY_BIPC = 0x10;
const   signed long WBEM_FLAG_RETURN_WHEN_COMPLETE_BIPC = 0x0;
const   signed long WBEM_FLAG_FORWARD_ONLY_BIPC = 0x20;
const   signed long WBEM_INFINITE_BIPC = 0xffffffffL;
const   signed long RPC_E_TOO_LATE_BIPC = 0x80010119L;
const   signed long S_OK_BIPC = 0L;
const   signed long S_FALSE_BIPC = 1;
const   signed long RPC_E_CHANGED_MODE_BIPC = 0x80010106L;
const unsigned long COINIT_APARTMENTTHREADED_BIPC   = 0x2;
const unsigned long COINIT_MULTITHREADED_BIPC       = 0x0;
const unsigned long COINIT_DISABLE_OLE1DDE_BIPC     = 0x4;
const unsigned long COINIT_SPEED_OVER_MEMORY_BIPC   = 0x4;

//If the user needs to change default COM initialization model,
//it can define BOOST_INTERPROCESS_WINDOWS_COINIT_MODEL to one of these:
//
// COINIT_APARTMENTTHREADED_BIPC
// COINIT_MULTITHREADED_BIPC
// COINIT_DISABLE_OLE1DDE_BIPC
// COINIT_SPEED_OVER_MEMORY_BIPC
#if !defined(BOOST_INTERPROCESS_WINDOWS_COINIT_MODEL)
   #define BOOST_INTERPROCESS_WINDOWS_COINIT_MODEL COINIT_APARTMENTTHREADED_BIPC
#elif (BOOST_INTERPROCESS_WINDOWS_COINIT_MODEL != COINIT_APARTMENTTHREADED_BIPC) &&\
      (BOOST_INTERPROCESS_WINDOWS_COINIT_MODEL != COINIT_MULTITHREADED_BIPC)     &&\
      (BOOST_INTERPROCESS_WINDOWS_COINIT_MODEL != COINIT_DISABLE_OLE1DDE_BIPC)   &&\
      (BOOST_INTERPROCESS_WINDOWS_COINIT_MODEL != COINIT_SPEED_OVER_MEMORY_BIPC)
   #error "Wrong value for BOOST_INTERPROCESS_WINDOWS_COINIT_MODEL macro"
#endif

}  //namespace winapi {
}  //namespace interprocess  {
}  //namespace boost  {


namespace boost  {
namespace interprocess  {
namespace winapi {

struct GUID_BIPC
{
   unsigned long  Data1;
   unsigned short Data2;
   unsigned short Data3;
   unsigned char  Data4[8];
};

const GUID_BIPC CLSID_WbemAdministrativeLocator =
   { 0xcb8555cc, 0x9128, 0x11d1, {0xad, 0x9b, 0x00, 0xc0, 0x4f, 0xd8, 0xfd, 0xff}};

const GUID_BIPC IID_IUnknown = { 0x00000000, 0x0000, 0x0000, {0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46}};

struct wchar_variant
{
   unsigned long  long dummy;
   union value_t{
      wchar_t *pbstrVal;
      unsigned long  long dummy;
   } value;
};

struct IUnknown_BIPC
{
   public:
   virtual long __stdcall QueryInterface(
      const GUID_BIPC &riid,  // [in]
      void **ppvObject) = 0;  // [iid_is][out]

   virtual unsigned long __stdcall AddRef (void) = 0;
   virtual unsigned long __stdcall Release(void) = 0;
};

struct IWbemClassObject_BIPC : public IUnknown_BIPC
{
   public:
   virtual long __stdcall GetQualifierSet(
      /* [out] */ void **ppQualSet) = 0;

   virtual long __stdcall Get(
      /* [string][in] */ const wchar_t * wszName,
      /* [in] */ long lFlags,
      /* [unique][in][out] */ wchar_variant *pVal,
      /* [unique][in][out] */ long *pType,
      /* [unique][in][out] */ long *plFlavor) = 0;

   virtual long __stdcall Put(
      /* [string][in] */ const wchar_t * wszName,
      /* [in] */ long lFlags,
      /* [in] */ wchar_variant *pVal,
      /* [in] */ long Type) = 0;

   virtual long __stdcall Delete(
      /* [string][in] */ const wchar_t * wszName) = 0;

   virtual long __stdcall GetNames(
      /* [string][in] */ const wchar_t * wszQualifierName,
      /* [in] */ long lFlags,
      /* [in] */ wchar_variant *pQualifierVal,
      /* [out] */ void * *pNames) = 0;

   virtual long __stdcall BeginEnumeration(
      /* [in] */ long lEnumFlags) = 0;

   virtual long __stdcall Next(
      /* [in] */ long lFlags,
      /* [unique][in][out] */ wchar_t * *strName,
      /* [unique][in][out] */ wchar_variant *pVal,
      /* [unique][in][out] */ long *pType,
      /* [unique][in][out] */ long *plFlavor) = 0;

   virtual long __stdcall EndEnumeration( void) = 0;

   virtual long __stdcall GetPropertyQualifierSet(
      /* [string][in] */ const wchar_t * wszProperty,
      /* [out] */ void **ppQualSet) = 0;

   virtual long __stdcall Clone(
      /* [out] */ IWbemClassObject_BIPC **ppCopy) = 0;

   virtual long __stdcall GetObjectText(
      /* [in] */ long lFlags,
      /* [out] */ wchar_t * *pstrObjectText) = 0;

   virtual long __stdcall SpawnDerivedClass(
      /* [in] */ long lFlags,
      /* [out] */ IWbemClassObject_BIPC **ppNewClass) = 0;

   virtual long __stdcall SpawnInstance(
      /* [in] */ long lFlags,
      /* [out] */ IWbemClassObject_BIPC **ppNewInstance) = 0;

   virtual long __stdcall CompareTo(
      /* [in] */ long lFlags,
      /* [in] */ IWbemClassObject_BIPC *pCompareTo) = 0;

   virtual long __stdcall GetPropertyOrigin(
      /* [string][in] */ const wchar_t * wszName,
      /* [out] */ wchar_t * *pstrClassName) = 0;

   virtual long __stdcall InheritsFrom(
      /* [in] */ const wchar_t * strAncestor) = 0;

   virtual long __stdcall GetMethod(
      /* [string][in] */ const wchar_t * wszName,
      /* [in] */ long lFlags,
      /* [out] */ IWbemClassObject_BIPC **ppInSignature,
      /* [out] */ IWbemClassObject_BIPC **ppOutSignature) = 0;

   virtual long __stdcall PutMethod(
      /* [string][in] */ const wchar_t * wszName,
      /* [in] */ long lFlags,
      /* [in] */ IWbemClassObject_BIPC *pInSignature,
      /* [in] */ IWbemClassObject_BIPC *pOutSignature) = 0;

   virtual long __stdcall DeleteMethod(
      /* [string][in] */ const wchar_t * wszName) = 0;

   virtual long __stdcall BeginMethodEnumeration(
      /* [in] */ long lEnumFlags) = 0;

   virtual long __stdcall NextMethod(
      /* [in] */ long lFlags,
      /* [unique][in][out] */ wchar_t * *pstrName,
      /* [unique][in][out] */ IWbemClassObject_BIPC **ppInSignature,
      /* [unique][in][out] */ IWbemClassObject_BIPC **ppOutSignature) = 0;

   virtual long __stdcall EndMethodEnumeration( void) = 0;

   virtual long __stdcall GetMethodQualifierSet(
      /* [string][in] */ const wchar_t * wszMethod,
      /* [out] */ void **ppQualSet) = 0;

   virtual long __stdcall GetMethodOrigin(
      /* [string][in] */ const wchar_t * wszMethodName,
      /* [out] */ wchar_t * *pstrClassName) = 0;

};

struct IWbemContext_BIPC : public IUnknown_BIPC
{
public:
   virtual long __stdcall Clone(
      /* [out] */ IWbemContext_BIPC **ppNewCopy) = 0;

   virtual long __stdcall GetNames(
      /* [in] */ long lFlags,
      /* [out] */ void * *pNames) = 0;

   virtual long __stdcall BeginEnumeration(
      /* [in] */ long lFlags) = 0;

   virtual long __stdcall Next(
      /* [in] */ long lFlags,
      /* [out] */ wchar_t * *pstrName,
      /* [out] */ wchar_variant *pValue) = 0;

   virtual long __stdcall EndEnumeration( void) = 0;

   virtual long __stdcall SetValue(
      /* [string][in] */ const wchar_t * wszName,
      /* [in] */ long lFlags,
      /* [in] */ wchar_variant *pValue) = 0;

   virtual long __stdcall GetValue(
      /* [string][in] */ const wchar_t * wszName,
      /* [in] */ long lFlags,
      /* [out] */ wchar_variant *pValue) = 0;

   virtual long __stdcall DeleteValue(
      /* [string][in] */ const wchar_t * wszName,
      /* [in] */ long lFlags) = 0;

   virtual long __stdcall DeleteAll( void) = 0;

};


struct IEnumWbemClassObject_BIPC : public IUnknown_BIPC
{
public:
   virtual long __stdcall Reset( void) = 0;

   virtual long __stdcall Next(
      /* [in] */ long lTimeout,
      /* [in] */ unsigned long uCount,
      /* [length_is][size_is][out] */ IWbemClassObject_BIPC **apObjects,
      /* [out] */ unsigned long *puReturned) = 0;

   virtual long __stdcall NextAsync(
      /* [in] */ unsigned long uCount,
      /* [in] */ void *pSink) = 0;

   virtual long __stdcall Clone(
      /* [out] */ void **ppEnum) = 0;

   virtual long __stdcall Skip(
      /* [in] */ long lTimeout,
      /* [in] */ unsigned long nCount) = 0;

};

struct IWbemServices_BIPC : public IUnknown_BIPC
{
public:
   virtual long __stdcall OpenNamespace(
      /* [in] */ const wchar_t * strNamespace,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [unique][in][out] */ void **ppWorkingNamespace,
      /* [unique][in][out] */ void **ppResult) = 0;

   virtual long __stdcall CancelAsyncCall(
      /* [in] */ void *pSink) = 0;

   virtual long __stdcall QueryObjectSink(
      /* [in] */ long lFlags,
      /* [out] */ void **ppResponseHandler) = 0;

   virtual long __stdcall GetObject(
      /* [in] */ const wchar_t * strObjectPath,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [unique][in][out] */ void **ppObject,
      /* [unique][in][out] */ void **ppCallResult) = 0;

   virtual long __stdcall GetObjectAsync(
      /* [in] */ const wchar_t * strObjectPath,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [in] */ void *pResponseHandler) = 0;

   virtual long __stdcall PutClass(
      /* [in] */ IWbemClassObject_BIPC *pObject,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [unique][in][out] */ void **ppCallResult) = 0;

   virtual long __stdcall PutClassAsync(
      /* [in] */ IWbemClassObject_BIPC *pObject,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [in] */ void *pResponseHandler) = 0;

   virtual long __stdcall DeleteClass(
      /* [in] */ const wchar_t * strClass,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [unique][in][out] */ void **ppCallResult) = 0;

   virtual long __stdcall DeleteClassAsync(
      /* [in] */ const wchar_t * strClass,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [in] */ void *pResponseHandler) = 0;

   virtual long __stdcall CreateClassEnum(
      /* [in] */ const wchar_t * strSuperclass,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [out] */ void **ppEnum) = 0;

   virtual long __stdcall CreateClassEnumAsync(
      /* [in] */ const wchar_t * strSuperclass,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [in] */ void *pResponseHandler) = 0;

   virtual long __stdcall PutInstance(
      /* [in] */ void *pInst,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [unique][in][out] */ void **ppCallResult) = 0;

   virtual long __stdcall PutInstanceAsync(
      /* [in] */ void *pInst,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [in] */ void *pResponseHandler) = 0;

   virtual long __stdcall DeleteInstance(
      /* [in] */ const wchar_t * strObjectPath,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [unique][in][out] */ void **ppCallResult) = 0;

   virtual long __stdcall DeleteInstanceAsync(
      /* [in] */ const wchar_t * strObjectPath,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [in] */ void *pResponseHandler) = 0;

   virtual long __stdcall CreateInstanceEnum(
      /* [in] */ const wchar_t * strFilter,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [out] */ void **ppEnum) = 0;

   virtual long __stdcall CreateInstanceEnumAsync(
      /* [in] */ const wchar_t * strFilter,
      /* [in] */ long lFlags,
      /* [in] */ void *pCtx,
      /* [in] */ void *pResponseHandler) = 0;

   virtual long __stdcall ExecQuery(
      /* [in] */ const wchar_t * strQueryLanguage,
      /* [in] */ const wchar_t * strQuery,
      /* [in] */ long lFlags,
      /* [in] */ IWbemContext_BIPC *pCtx,
      /* [out] */ IEnumWbemClassObject_BIPC **ppEnum) = 0;

   virtual long __stdcall ExecQueryAsync(
      /* [in] */ const wchar_t * strQueryLanguage,
      /* [in] */ const wchar_t * strQuery,
      /* [in] */ long lFlags,
      /* [in] */ IWbemContext_BIPC *pCtx,
      /* [in] */ void *pResponseHandler) = 0;

   virtual long __stdcall ExecNotificationQuery(
      /* [in] */ const wchar_t * strQueryLanguage,
      /* [in] */ const wchar_t * strQuery,
      /* [in] */ long lFlags,
      /* [in] */ IWbemContext_BIPC *pCtx,
      /* [out] */ void **ppEnum) = 0;

   virtual long __stdcall ExecNotificationQueryAsync(
      /* [in] */ const wchar_t * strQueryLanguage,
      /* [in] */ const wchar_t * strQuery,
      /* [in] */ long lFlags,
      /* [in] */ IWbemContext_BIPC *pCtx,
      /* [in] */ void *pResponseHandler) = 0;

   virtual long __stdcall ExecMethod(
      /* [in] */ const wchar_t * strObjectPath,
      /* [in] */ const wchar_t * strMethodName,
      /* [in] */ long lFlags,
      /* [in] */ IWbemContext_BIPC *pCtx,
      /* [in] */ IWbemClassObject_BIPC *pInParams,
      /* [unique][in][out] */ IWbemClassObject_BIPC **ppOutParams,
      /* [unique][in][out] */ void **ppCallResult) = 0;

   virtual long __stdcall ExecMethodAsync(
      /* [in] */ const wchar_t * strObjectPath,
      /* [in] */ const wchar_t * strMethodName,
      /* [in] */ long lFlags,
      /* [in] */ IWbemContext_BIPC *pCtx,
      /* [in] */ IWbemClassObject_BIPC *pInParams,
      /* [in] */ void *pResponseHandler) = 0;

};

struct IWbemLocator_BIPC : public IUnknown_BIPC
{
public:
   virtual long __stdcall ConnectServer(
      /* [in] */ const wchar_t * strNetworkResource,
      /* [in] */ const wchar_t * strUser,
      /* [in] */ const wchar_t * strPassword,
      /* [in] */ const wchar_t * strLocale,
      /* [in] */ long lSecurityFlags,
      /* [in] */ const wchar_t * strAuthority,
      /* [in] */ void *pCtx,
      /* [out] */ IWbemServices_BIPC **ppNamespace) = 0;

};

struct interprocess_overlapped
{
   unsigned long *internal;
   unsigned long *internal_high;
   union {
      struct {
         unsigned long offset;
         unsigned long offset_high;
      }dummy;
      void *pointer;
   };

   void *h_event;
};

struct interprocess_semaphore_basic_information
{
	unsigned int count;		// current semaphore count
	unsigned int limit;		// max semaphore count
};

struct interprocess_section_basic_information
{
  void *          base_address;
  unsigned long   section_attributes;
  __int64         section_size;
};

struct interprocess_filetime
{
   unsigned long  dwLowDateTime;
   unsigned long  dwHighDateTime;
};

struct win32_find_data_t
{
   unsigned long dwFileAttributes;
   interprocess_filetime ftCreationTime;
   interprocess_filetime ftLastAccessTime;
   interprocess_filetime ftLastWriteTime;
   unsigned long nFileSizeHigh;
   unsigned long nFileSizeLow;
   unsigned long dwReserved0;
   unsigned long dwReserved1;
   char cFileName[MaxPath];
   char cAlternateFileName[14];
};

struct interprocess_security_attributes
{
   unsigned long nLength;
   void *lpSecurityDescriptor;
   int bInheritHandle;
};

struct system_info {
    union {
        unsigned long dwOemId;          // Obsolete field...do not use
        struct {
            unsigned short wProcessorArchitecture;
            unsigned short wReserved;
        } dummy;
    };
    unsigned long dwPageSize;
    void * lpMinimumApplicationAddress;
    void * lpMaximumApplicationAddress;
    unsigned long * dwActiveProcessorMask;
    unsigned long dwNumberOfProcessors;
    unsigned long dwProcessorType;
    unsigned long dwAllocationGranularity;
    unsigned short wProcessorLevel;
    unsigned short wProcessorRevision;
};

struct interprocess_memory_basic_information
{
   void *         BaseAddress;
   void *         AllocationBase;
   unsigned long  AllocationProtect;
   unsigned long  RegionSize;
   unsigned long  State;
   unsigned long  Protect;
   unsigned long  Type;
};

struct interprocess_acl
{
   unsigned char  AclRevision;
   unsigned char  Sbz1;
   unsigned short AclSize;
   unsigned short AceCount;
   unsigned short Sbz2;
};

typedef struct _interprocess_security_descriptor
{
   unsigned char Revision;
   unsigned char Sbz1;
   unsigned short Control;
   void *Owner;
   void *Group;
   interprocess_acl *Sacl;
   interprocess_acl *Dacl;
} interprocess_security_descriptor;

enum file_information_class_t {
   file_directory_information = 1,
   file_full_directory_information,
   file_both_directory_information,
   file_basic_information,
   file_standard_information,
   file_internal_information,
   file_ea_information,
   file_access_information,
   file_name_information,
   file_rename_information,
   file_link_information,
   file_names_information,
   file_disposition_information,
   file_position_information,
   file_full_ea_information,
   file_mode_information,
   file_alignment_information,
   file_all_information,
   file_allocation_information,
   file_end_of_file_information,
   file_alternate_name_information,
   file_stream_information,
   file_pipe_information,
   file_pipe_local_information,
   file_pipe_remote_information,
   file_mailslot_query_information,
   file_mailslot_set_information,
   file_compression_information,
   file_copy_on_write_information,
   file_completion_information,
   file_move_cluster_information,
   file_quota_information,
   file_reparse_point_information,
   file_network_open_information,
   file_object_id_information,
   file_tracking_information,
   file_ole_directory_information,
   file_content_index_information,
   file_inherit_content_index_information,
   file_ole_information,
   file_maximum_information
};

enum semaphore_information_class {
   semaphore_basic_information = 0
};

struct file_name_information_t {
   unsigned long FileNameLength;
   wchar_t FileName[1];
};

struct file_rename_information_t {
   int Replace;
   void *RootDir;
   unsigned long FileNameLength;
   wchar_t FileName[1];
};

struct unicode_string_t {
   unsigned short Length;
   unsigned short MaximumLength;
   wchar_t *Buffer;
};

struct object_attributes_t {
   unsigned long Length;
   void * RootDirectory;
   unicode_string_t *ObjectName;
   unsigned long Attributes;
   void *SecurityDescriptor;
   void *SecurityQualityOfService;
};

struct io_status_block_t {
   union {
      long Status;
      void *Pointer;
   };

   unsigned long *Information;
};

union system_timeofday_information
{
   struct data_t
   {
      __int64 liKeBootTime;
      __int64 liKeSystemTime;
      __int64 liExpTimeZoneBias;
      unsigned long uCurrentTimeZoneId;
      unsigned long dwReserved;
   } data;
   unsigned char Reserved1[SystemTimeOfDayInfoLength];
};

struct interprocess_by_handle_file_information
{
    unsigned long dwFileAttributes;
    interprocess_filetime ftCreationTime;
    interprocess_filetime ftLastAccessTime;
    interprocess_filetime ftLastWriteTime;
    unsigned long dwVolumeSerialNumber;
    unsigned long nFileSizeHigh;
    unsigned long nFileSizeLow;
    unsigned long nNumberOfLinks;
    unsigned long nFileIndexHigh;
    unsigned long nFileIndexLow;
};

enum system_information_class {
   system_basic_information = 0,
   system_performance_information = 2,
   system_time_of_day_information = 3,
   system_process_information = 5,
   system_processor_performance_information = 8,
   system_interrupt_information = 23,
   system_exception_information = 33,
   system_registry_quota_information = 37,
   system_lookaside_information = 45
};

enum object_information_class
{
   object_basic_information,
   object_name_information,
   object_type_information,
   object_all_information,
   object_data_information
};

enum section_information_class
{
   section_basic_information,
   section_image_information
};

struct object_name_information_t
{
   unicode_string_t Name;
   wchar_t NameBuffer[1];
};

//Some windows API declarations
extern "C" __declspec(dllimport) unsigned long __stdcall GetCurrentProcessId();
extern "C" __declspec(dllimport) unsigned long __stdcall GetCurrentThreadId();
extern "C" __declspec(dllimport) int __stdcall GetProcessTimes
   ( void *hProcess, interprocess_filetime* lpCreationTime
   , interprocess_filetime *lpExitTime,interprocess_filetime *lpKernelTime
   , interprocess_filetime *lpUserTime );
extern "C" __declspec(dllimport) void __stdcall Sleep(unsigned long);
extern "C" __declspec(dllimport) int __stdcall SwitchToThread();
extern "C" __declspec(dllimport) unsigned long __stdcall GetLastError();
extern "C" __declspec(dllimport) void __stdcall SetLastError(unsigned long);
extern "C" __declspec(dllimport) void * __stdcall GetCurrentProcess();
extern "C" __declspec(dllimport) int __stdcall CloseHandle(void*);
extern "C" __declspec(dllimport) int __stdcall DuplicateHandle
   ( void *hSourceProcessHandle,    void *hSourceHandle
   , void *hTargetProcessHandle,    void **lpTargetHandle
   , unsigned long dwDesiredAccess, int bInheritHandle
   , unsigned long dwOptions);
extern "C" __declspec(dllimport) long __stdcall GetFileType(void *hFile);
extern "C" __declspec(dllimport) void *__stdcall FindFirstFileA(const char *lpFileName, win32_find_data_t *lpFindFileData);
extern "C" __declspec(dllimport) int   __stdcall FindNextFileA(void *hFindFile, win32_find_data_t *lpFindFileData);
extern "C" __declspec(dllimport) int   __stdcall FindClose(void *hFindFile);
//extern "C" __declspec(dllimport) void __stdcall GetSystemTimeAsFileTime(interprocess_filetime*);
//extern "C" __declspec(dllimport) int  __stdcall FileTimeToLocalFileTime(const interprocess_filetime *in, const interprocess_filetime *out);
extern "C" __declspec(dllimport) void * __stdcall CreateMutexA(interprocess_security_attributes*, int, const char *);
extern "C" __declspec(dllimport) void * __stdcall OpenMutexA(unsigned long, int, const char *);
extern "C" __declspec(dllimport) unsigned long __stdcall WaitForSingleObject(void *, unsigned long);
extern "C" __declspec(dllimport) int __stdcall ReleaseMutex(void *);
extern "C" __declspec(dllimport) int __stdcall UnmapViewOfFile(void *);
extern "C" __declspec(dllimport) void * __stdcall CreateSemaphoreA(interprocess_security_attributes*, long, long, const char *);
extern "C" __declspec(dllimport) int __stdcall ReleaseSemaphore(void *, long, long *);
extern "C" __declspec(dllimport) void * __stdcall OpenSemaphoreA(unsigned long, int, const char *);
extern "C" __declspec(dllimport) void * __stdcall CreateFileMappingA (void *, interprocess_security_attributes*, unsigned long, unsigned long, unsigned long, const char *);
extern "C" __declspec(dllimport) void * __stdcall MapViewOfFileEx (void *, unsigned long, unsigned long, unsigned long, std::size_t, void*);
extern "C" __declspec(dllimport) void * __stdcall OpenFileMappingA (unsigned long, int, const char *);
extern "C" __declspec(dllimport) void * __stdcall CreateFileA (const char *, unsigned long, unsigned long, struct interprocess_security_attributes*, unsigned long, unsigned long, void *);
extern "C" __declspec(dllimport) int __stdcall    DeleteFileA (const char *);
extern "C" __declspec(dllimport) int __stdcall    MoveFileExA (const char *, const char *, unsigned long);
extern "C" __declspec(dllimport) void __stdcall GetSystemInfo (struct system_info *);
extern "C" __declspec(dllimport) int __stdcall FlushViewOfFile (void *, std::size_t);
extern "C" __declspec(dllimport) int __stdcall VirtualUnlock (void *, std::size_t);
extern "C" __declspec(dllimport) int __stdcall VirtualProtect (void *, std::size_t, unsigned long, unsigned long *);
extern "C" __declspec(dllimport) int __stdcall FlushFileBuffers (void *);
extern "C" __declspec(dllimport) int __stdcall GetFileSizeEx (void *, __int64 *size);
extern "C" __declspec(dllimport) unsigned long __stdcall FormatMessageA
   (unsigned long dwFlags,       const void *lpSource,   unsigned long dwMessageId,
   unsigned long dwLanguageId,   char *lpBuffer,         unsigned long nSize,
   std::va_list *Arguments);
extern "C" __declspec(dllimport) void *__stdcall LocalFree (void *);
extern "C" __declspec(dllimport) unsigned long __stdcall GetFileAttributesA(const char *);
extern "C" __declspec(dllimport) int __stdcall CreateDirectoryA(const char *, interprocess_security_attributes*);
extern "C" __declspec(dllimport) int __stdcall RemoveDirectoryA(const char *lpPathName);
extern "C" __declspec(dllimport) int __stdcall GetTempPathA(unsigned long length, char *buffer);
extern "C" __declspec(dllimport) int __stdcall CreateDirectory(const char *, interprocess_security_attributes*);
extern "C" __declspec(dllimport) int __stdcall SetFileValidData(void *, __int64 size);
extern "C" __declspec(dllimport) int __stdcall SetEndOfFile(void *);
extern "C" __declspec(dllimport) int __stdcall SetFilePointerEx(void *, __int64 distance, __int64 *new_file_pointer, unsigned long move_method);
extern "C" __declspec(dllimport) int __stdcall LockFile  (void *hnd, unsigned long offset_low, unsigned long offset_high, unsigned long size_low, unsigned long size_high);
extern "C" __declspec(dllimport) int __stdcall UnlockFile(void *hnd, unsigned long offset_low, unsigned long offset_high, unsigned long size_low, unsigned long size_high);
extern "C" __declspec(dllimport) int __stdcall LockFileEx(void *hnd, unsigned long flags, unsigned long reserved, unsigned long size_low, unsigned long size_high, interprocess_overlapped* overlapped);
extern "C" __declspec(dllimport) int __stdcall UnlockFileEx(void *hnd, unsigned long reserved, unsigned long size_low, unsigned long size_high, interprocess_overlapped* overlapped);
extern "C" __declspec(dllimport) int __stdcall WriteFile(void *hnd, const void *buffer, unsigned long bytes_to_write, unsigned long *bytes_written, interprocess_overlapped* overlapped);
extern "C" __declspec(dllimport) int __stdcall ReadFile(void *hnd, void *buffer, unsigned long bytes_to_read, unsigned long *bytes_read, interprocess_overlapped* overlapped);
extern "C" __declspec(dllimport) int __stdcall InitializeSecurityDescriptor(interprocess_security_descriptor *pSecurityDescriptor, unsigned long dwRevision);
extern "C" __declspec(dllimport) int __stdcall SetSecurityDescriptorDacl(interprocess_security_descriptor *pSecurityDescriptor, int bDaclPresent, interprocess_acl *pDacl, int bDaclDefaulted);
extern "C" __declspec(dllimport) void *__stdcall LoadLibraryA(const char *);
extern "C" __declspec(dllimport) int   __stdcall FreeLibrary(void *);
extern "C" __declspec(dllimport) void *__stdcall GetProcAddress(void *, const char*);
extern "C" __declspec(dllimport) void *__stdcall GetModuleHandleA(const char*);
extern "C" __declspec(dllimport) void *__stdcall GetFileInformationByHandle(void *, interprocess_by_handle_file_information*);
extern "C" __declspec(dllimport) unsigned long __stdcall GetMappedFileNameW(void *, void *, wchar_t *, unsigned long);
extern "C" __declspec(dllimport) long __stdcall RegOpenKeyExA(void *, const char *, unsigned long, unsigned long, void **);
extern "C" __declspec(dllimport) long __stdcall RegQueryValueExA(void *, const char *, unsigned long*, unsigned long*, unsigned char *, unsigned long*);
extern "C" __declspec(dllimport) long __stdcall RegCloseKey(void *);
extern "C" __declspec(dllimport) int  __stdcall QueryPerformanceCounter(__int64 *lpPerformanceCount);

//COM API
extern "C" __declspec(dllimport) long __stdcall CoInitializeEx(void *pvReserved, unsigned long dwCoInit);
extern "C" __declspec(dllimport) long __stdcall CoInitializeSecurity(
                    void*          pSecDesc,
                    long           cAuthSvc,
                    void *         asAuthSvc,
                    void          *pReserved1,
                    unsigned long  dwAuthnLevel,
                    unsigned long  dwImpLevel,
                    void          *pAuthList,
                    unsigned long  dwCapabilities,
                    void          *pReserved3 );

 extern "C" __declspec(dllimport) long __stdcall CoSetProxyBlanket(
                     IUnknown_BIPC *pProxy,
                     unsigned long dwAuthnSvc,
                     unsigned long dwAuthzSvc,
                     wchar_t *pServerPrincName,
                     unsigned long dwAuthnLevel,
                     unsigned long dwImpLevel,
                     void *pAuthInfo,
                     unsigned long dwCapabilities);

extern "C" __declspec(dllimport) long __stdcall VariantClear(wchar_variant * pvarg);
extern "C" __declspec(dllimport) long __stdcall CoCreateInstance(const GUID_BIPC & rclsid, IUnknown_BIPC *pUnkOuter,
                    unsigned long dwClsContext, const GUID_BIPC & riid, void** ppv);
extern "C" __declspec(dllimport) void __stdcall CoUninitialize(void);



//API function typedefs
//Pointer to functions
typedef long (__stdcall *NtDeleteFile_t)(object_attributes_t *ObjectAttributes);
typedef long (__stdcall *NtSetInformationFile_t)(void *FileHandle, io_status_block_t *IoStatusBlock, void *FileInformation, unsigned long Length, int FileInformationClass );
typedef long (__stdcall *NtQuerySystemInformation_t)(int, void*, unsigned long, unsigned long *);
typedef long (__stdcall *NtQueryObject_t)(void*, object_information_class, void *, unsigned long, unsigned long *);
typedef long (__stdcall *NtQuerySemaphore_t)(void*, unsigned int info_class, interprocess_semaphore_basic_information *pinfo, unsigned int info_size, unsigned int *ret_len);
typedef long (__stdcall *NtQuerySection_t)(void*, section_information_class, interprocess_section_basic_information *pinfo, unsigned long info_size, unsigned long *ret_len);
typedef long (__stdcall *NtQueryInformationFile_t)(void *,io_status_block_t *,void *, long, int);
typedef long (__stdcall *NtOpenFile_t)(void*,unsigned long ,object_attributes_t*,io_status_block_t*,unsigned long,unsigned long);
typedef long (__stdcall *NtClose_t) (void*);
typedef long (__stdcall *RtlCreateUnicodeStringFromAsciiz_t)(unicode_string_t *, const char *);
typedef void (__stdcall *RtlFreeUnicodeString_t)(unicode_string_t *);
typedef void (__stdcall *RtlInitUnicodeString_t)( unicode_string_t *, const wchar_t * );
typedef long (__stdcall *RtlAppendUnicodeToString_t)(unicode_string_t *Destination, const wchar_t *Source);
typedef unsigned long (__stdcall * GetMappedFileName_t)(void *, void *, wchar_t *, unsigned long);
typedef long          (__stdcall * RegOpenKeyEx_t)(void *, const char *, unsigned long, unsigned long, void **);
typedef long          (__stdcall * RegQueryValueEx_t)(void *, const char *, unsigned long*, unsigned long*, unsigned char *, unsigned long*);
typedef long          (__stdcall * RegCloseKey_t)(void *);

}  //namespace winapi {
}  //namespace interprocess  {
}  //namespace boost  {

namespace boost {
namespace interprocess {
namespace winapi {

inline unsigned long get_last_error()
{  return GetLastError();  }

inline void set_last_error(unsigned long err)
{  return SetLastError(err);  }

inline unsigned long format_message
   (unsigned long dwFlags, const void *lpSource,
    unsigned long dwMessageId, unsigned long dwLanguageId,
    char *lpBuffer, unsigned long nSize, std::va_list *Arguments)
{
   return FormatMessageA
      (dwFlags, lpSource, dwMessageId, dwLanguageId, lpBuffer, nSize, Arguments);
}

//And now, wrapper functions
inline void * local_free(void *hmem)
{  return LocalFree(hmem); }

inline unsigned long make_lang_id(unsigned long p, unsigned long s)
{  return ((((unsigned short)(s)) << 10) | (unsigned short)(p));   }

inline void sched_yield()
{
   if(!SwitchToThread()){
      Sleep(1);
   }
}

inline void sleep(unsigned long ms)
{  Sleep(ms);  }

inline unsigned long get_current_thread_id()
{  return GetCurrentThreadId();  }

inline bool get_process_times
   ( void *hProcess, interprocess_filetime* lpCreationTime
   , interprocess_filetime *lpExitTime, interprocess_filetime *lpKernelTime
   , interprocess_filetime *lpUserTime )
{  return 0 != GetProcessTimes(hProcess, lpCreationTime, lpExitTime, lpKernelTime, lpUserTime); }

inline unsigned long get_current_process_id()
{  return GetCurrentProcessId();  }

inline unsigned int close_handle(void* handle)
{  return CloseHandle(handle);   }

inline void * find_first_file(const char *lpFileName, win32_find_data_t *lpFindFileData)
{  return FindFirstFileA(lpFileName, lpFindFileData);   }

inline bool find_next_file(void *hFindFile, win32_find_data_t *lpFindFileData)
{  return FindNextFileA(hFindFile, lpFindFileData) != 0;   }

inline bool find_close(void *handle)
{  return FindClose(handle) != 0;   }

inline bool duplicate_current_process_handle
   (void *hSourceHandle, void **lpTargetHandle)
{
   return 0 != DuplicateHandle
      ( GetCurrentProcess(),  hSourceHandle,    GetCurrentProcess()
      , lpTargetHandle,       0,                0
      , duplicate_same_access);
}

inline unsigned long get_file_type(void *hFile)
{
   return GetFileType(hFile);
}

/*
inline void get_system_time_as_file_time(interprocess_filetime *filetime)
{  GetSystemTimeAsFileTime(filetime);  }

inline bool file_time_to_local_file_time
   (const interprocess_filetime *in, const interprocess_filetime *out)
{  return 0 != FileTimeToLocalFileTime(in, out);  }
*/
inline void *open_or_create_mutex(const char *name, bool initial_owner, interprocess_security_attributes *attr)
{  return CreateMutexA(attr, (int)initial_owner, name);  }

inline unsigned long wait_for_single_object(void *handle, unsigned long time)
{  return WaitForSingleObject(handle, time); }

inline int release_mutex(void *handle)
{  return ReleaseMutex(handle);  }

inline int unmap_view_of_file(void *address)
{  return UnmapViewOfFile(address); }

inline void *open_or_create_semaphore(const char *name, long initial_count, long maximum_count, interprocess_security_attributes *attr)
{  return CreateSemaphoreA(attr, initial_count, maximum_count, name);  }

inline void *open_semaphore(const char *name)
{  return OpenSemaphoreA(semaphore_all_access, 0, name);  }

inline int release_semaphore(void *handle, long release_count, long *prev_count)
{  return ReleaseSemaphore(handle, release_count, prev_count); }

class interprocess_all_access_security
{
   interprocess_security_attributes sa;
   interprocess_security_descriptor sd;
   bool initialized;

   public:
   interprocess_all_access_security()
      : initialized(false)
   {
      if(!InitializeSecurityDescriptor(&sd, security_descriptor_revision))
         return;
      if(!SetSecurityDescriptorDacl(&sd, true, 0, false))
         return;
      sa.lpSecurityDescriptor = &sd;
      sa.nLength = sizeof(interprocess_security_attributes);
      sa.bInheritHandle = false;
      initialized = false;
   }

   interprocess_security_attributes *get_attributes()
   {  return &sa; }
};

inline void * create_file_mapping (void * handle, unsigned long access, unsigned __int64 file_offset, const char * name, interprocess_security_attributes *psec)
{
   const unsigned long high_size(file_offset >> 32), low_size((boost::uint32_t)file_offset);
   return CreateFileMappingA (handle, psec, access, high_size, low_size, name);
}

inline void * open_file_mapping (unsigned long access, const char *name)
{  return OpenFileMappingA (access, 0, name);   }

inline void *map_view_of_file_ex(void *handle, unsigned long file_access, unsigned __int64 offset, std::size_t numbytes, void *base_addr)
{
   const unsigned long offset_low  = (unsigned long)(offset & ((unsigned __int64)0xFFFFFFFF));
   const unsigned long offset_high = offset >> 32;
   return MapViewOfFileEx(handle, file_access, offset_high, offset_low, numbytes, base_addr);
}

inline void *create_file(const char *name, unsigned long access, unsigned long creation_flags, unsigned long attributes, interprocess_security_attributes *psec)
{
   for (unsigned int attempt(0); attempt < error_sharing_violation_tries; ++attempt){
      void * const handle = CreateFileA(name, access,
                                        file_share_read | file_share_write | file_share_delete,
                                        psec, creation_flags, attributes, 0);
      bool const invalid(invalid_handle_value == handle);
      if (!invalid){
         return handle;
      }
      if (error_sharing_violation != get_last_error()){
         return handle;
      }
      sleep(error_sharing_violation_sleep_ms);
   }
   return invalid_handle_value;
}

inline bool delete_file(const char *name)
{  return 0 != DeleteFileA(name);  }

inline bool move_file_ex(const char *source_filename, const char *destination_filename, unsigned long flags)
{  return 0 != MoveFileExA(source_filename, destination_filename, flags);  }

inline void get_system_info(system_info *info)
{  GetSystemInfo(info); }

inline bool flush_view_of_file(void *base_addr, std::size_t numbytes)
{  return 0 != FlushViewOfFile(base_addr, numbytes); }

inline bool virtual_unlock(void *base_addr, std::size_t numbytes)
{  return 0 != VirtualUnlock(base_addr, numbytes); }

inline bool virtual_protect(void *base_addr, std::size_t numbytes, unsigned long flNewProtect, unsigned long &lpflOldProtect)
{  return 0 != VirtualProtect(base_addr, numbytes, flNewProtect, &lpflOldProtect); }

inline bool flush_file_buffers(void *handle)
{  return 0 != FlushFileBuffers(handle); }

inline bool get_file_size(void *handle, __int64 &size)
{  return 0 != GetFileSizeEx(handle, &size);  }

inline bool create_directory(const char *name)
{
   interprocess_all_access_security sec;
   return 0 != CreateDirectoryA(name, sec.get_attributes());
}

inline bool remove_directory(const char *lpPathName)
{  return 0 != RemoveDirectoryA(lpPathName);   }

inline unsigned long get_temp_path(unsigned long length, char *buffer)
{  return GetTempPathA(length, buffer);   }

inline int set_end_of_file(void *handle)
{  return 0 != SetEndOfFile(handle);   }

inline bool set_file_pointer_ex(void *handle, __int64 distance, __int64 *new_file_pointer, unsigned long move_method)
{  return 0 != SetFilePointerEx(handle, distance, new_file_pointer, move_method);   }

inline bool lock_file_ex(void *hnd, unsigned long flags, unsigned long reserved, unsigned long size_low, unsigned long size_high, interprocess_overlapped *overlapped)
{  return 0 != LockFileEx(hnd, flags, reserved, size_low, size_high, overlapped); }

inline bool unlock_file_ex(void *hnd, unsigned long reserved, unsigned long size_low, unsigned long size_high, interprocess_overlapped *overlapped)
{  return 0 != UnlockFileEx(hnd, reserved, size_low, size_high, overlapped);  }

inline bool write_file(void *hnd, const void *buffer, unsigned long bytes_to_write, unsigned long *bytes_written, interprocess_overlapped* overlapped)
{  return 0 != WriteFile(hnd, buffer, bytes_to_write, bytes_written, overlapped);  }

inline bool read_file(void *hnd, void *buffer, unsigned long bytes_to_read, unsigned long *bytes_read, interprocess_overlapped* overlapped)
{  return 0 != ReadFile(hnd, buffer, bytes_to_read, bytes_read, overlapped);  }

inline bool get_file_information_by_handle(void *hnd, interprocess_by_handle_file_information *info)
{  return 0 != GetFileInformationByHandle(hnd, info);  }

inline long interlocked_increment(long volatile *addr)
{  return BOOST_INTERLOCKED_INCREMENT(addr);  }

inline long interlocked_decrement(long volatile *addr)
{  return BOOST_INTERLOCKED_DECREMENT(addr);  }

inline long interlocked_compare_exchange(long volatile *addr, long val1, long val2)
{  return BOOST_INTERLOCKED_COMPARE_EXCHANGE(addr, val1, val2);  }

inline long interlocked_exchange_add(long volatile* addend, long value)
{  return BOOST_INTERLOCKED_EXCHANGE_ADD(const_cast<long*>(addend), value);  }

inline long interlocked_exchange(long volatile* addend, long value)
{  return BOOST_INTERLOCKED_EXCHANGE(const_cast<long*>(addend), value);  }

//Forward functions
inline void *load_library(const char *name)
{  return LoadLibraryA(name); }

inline bool free_library(void *module)
{  return 0 != FreeLibrary(module); }

inline void *get_proc_address(void *module, const char *name)
{  return GetProcAddress(module, name); }

inline void *get_current_process()
{  return GetCurrentProcess();  }

inline void *get_module_handle(const char *name)
{  return GetModuleHandleA(name); }

inline unsigned long get_mapped_file_name(void *process, void *lpv, wchar_t *lpfilename, unsigned long nSize)
{  return GetMappedFileNameW(process, lpv, lpfilename, nSize); }

inline long reg_open_key_ex(void *hKey, const char *lpSubKey, unsigned long ulOptions, unsigned long samDesired, void **phkResult)
{  return RegOpenKeyExA(hKey, lpSubKey, ulOptions, samDesired, phkResult); }

inline long reg_query_value_ex(void *hKey, const char *lpValueName, unsigned long*lpReserved, unsigned long*lpType, unsigned char *lpData, unsigned long*lpcbData)
{  return RegQueryValueExA(hKey, lpValueName, lpReserved, lpType, lpData, lpcbData); }

inline long reg_close_key(void *hKey)
{  return RegCloseKey(hKey); }

inline bool query_performance_counter(__int64 *lpPerformanceCount)
{
   return 0 != QueryPerformanceCounter(lpPerformanceCount);
}

inline void initialize_object_attributes
( object_attributes_t *pobject_attr, unicode_string_t *name
 , unsigned long attr, void *rootdir, void *security_descr)

{
   pobject_attr->Length = sizeof(object_attributes_t);
   pobject_attr->RootDirectory = rootdir;
   pobject_attr->Attributes = attr;
   pobject_attr->ObjectName = name;
   pobject_attr->SecurityDescriptor = security_descr;
   pobject_attr->SecurityQualityOfService = 0;
}

inline void rtl_init_empty_unicode_string(unicode_string_t *ucStr, wchar_t *buf, unsigned short bufSize)
{
   ucStr->Buffer = buf;
   ucStr->Length = 0;
   ucStr->MaximumLength = bufSize;
}

//A class that locates and caches loaded DLL function addresses.
template<int Dummy>
struct function_address_holder
{
   enum { NtSetInformationFile, NtQuerySystemInformation, NtQueryObject, NtQuerySemaphore, NtQuerySection, NumFunction };
   enum { NtDll_dll, NumModule };

   private:
   static void *FunctionAddresses[NumFunction];
   static volatile long FunctionStates[NumFunction];
   static void *ModuleAddresses[NumModule];
   static volatile long ModuleStates[NumModule];

   static void *get_module_from_id(unsigned int id)
   {
      assert(id < (unsigned int)NumModule);
      const char *module[] = { "ntdll.dll" };
      bool compile_check[sizeof(module)/sizeof(module[0]) == NumModule];
      (void)compile_check;
      return get_module_handle(module[id]);
   }

   static void *get_module(const unsigned int id)
   {
      assert(id < (unsigned int)NumModule);
      while(ModuleStates[id] < 2){
         if(interlocked_compare_exchange(&ModuleStates[id], 1, 0) == 0){
            ModuleAddresses[id] = get_module_from_id(id);
            interlocked_increment(&ModuleStates[id]);
            break;
         }
         else{
            sched_yield();
         }
      }
      return ModuleAddresses[id];
   }

   static void *get_address_from_dll(const unsigned int id)
   {
      assert(id < (unsigned int)NumFunction);
      const char *function[] = { "NtSetInformationFile", "NtQuerySystemInformation", "NtQueryObject", "NtQuerySemaphore", "NtQuerySection" };
      bool compile_check[sizeof(function)/sizeof(function[0]) == NumFunction];
      (void)compile_check;
      return get_proc_address(get_module(NtDll_dll), function[id]);
   }

   public:
   static void *get(const unsigned int id)
   {
      assert(id < (unsigned int)NumFunction);
      while(FunctionStates[id] < 2){
         if(interlocked_compare_exchange(&FunctionStates[id], 1, 0) == 0){
            FunctionAddresses[id] = get_address_from_dll(id);
            interlocked_increment(&FunctionStates[id]);
            break;
         }
         else{
            sched_yield();
         }
      }
      return FunctionAddresses[id];
   }
};

template<int Dummy>
void *function_address_holder<Dummy>::FunctionAddresses[function_address_holder<Dummy>::NumFunction];

template<int Dummy>
volatile long function_address_holder<Dummy>::FunctionStates[function_address_holder<Dummy>::NumFunction];

template<int Dummy>
void *function_address_holder<Dummy>::ModuleAddresses[function_address_holder<Dummy>::NumModule];

template<int Dummy>
volatile long function_address_holder<Dummy>::ModuleStates[function_address_holder<Dummy>::NumModule];


struct dll_func
   : public function_address_holder<0>
{};

//Complex winapi based functions...
struct library_unloader
{
   void *lib_;
   library_unloader(void *module) : lib_(module){}
   ~library_unloader(){ free_library(lib_);  }
};

//pszFilename must have room for at least MaxPath+1 characters
inline bool get_file_name_from_handle_function
   (void * hFile, wchar_t *pszFilename, std::size_t length, std::size_t &out_length)
{
   if(length <= MaxPath){
      return false;
   }

//   void *hiPSAPI = load_library("PSAPI.DLL");
//   if (0 == hiPSAPI)
//      return 0;
//   library_unloader unloader(hiPSAPI);

//  Pointer to function getMappedFileName() in PSAPI.DLL
//   GetMappedFileName_t pfGMFN =
//      (GetMappedFileName_t)get_proc_address(hiPSAPI, "GetMappedFileNameW");
//   if (! pfGMFN){
//      return 0;      //  Failed: unexpected error
//   }

   bool bSuccess = false;

   // Create a file mapping object.
   void * hFileMap = create_file_mapping(hFile, page_readonly, 1, 0, 0);
   if(hFileMap){
      // Create a file mapping to get the file name.
      void* pMem = map_view_of_file_ex(hFileMap, file_map_read, 0, 1, 0);

      if (pMem){
         //out_length = pfGMFN(get_current_process(), pMem, pszFilename, MaxPath);
         out_length = get_mapped_file_name(get_current_process(), pMem, pszFilename, MaxPath);
         if(out_length){
            bSuccess = true;
         }
         unmap_view_of_file(pMem);
      }
      close_handle(hFileMap);
   }

   return(bSuccess);
}

inline bool get_system_time_of_day_information(system_timeofday_information &info)
{
   NtQuerySystemInformation_t pNtQuerySystemInformation = (NtQuerySystemInformation_t)
         dll_func::get(dll_func::NtQuerySystemInformation);
   unsigned long res;
   long status = pNtQuerySystemInformation(system_time_of_day_information, &info, sizeof(info), &res);
   if(status){
      return false;
   }
   return true;
}

inline bool get_boot_time(unsigned char (&bootstamp) [BootstampLength])
{
   system_timeofday_information info;
   bool ret = get_system_time_of_day_information(info);
   if(!ret){
      return false;
   }
   std::memcpy(&bootstamp[0], &info.Reserved1, sizeof(bootstamp));
   return true;
}

inline bool get_boot_and_system_time(unsigned char (&bootsystemstamp) [BootAndSystemstampLength])
{
   system_timeofday_information info;
   bool ret = get_system_time_of_day_information(info);
   if(!ret){
      return false;
   }
   std::memcpy(&bootsystemstamp[0], &info.Reserved1, sizeof(bootsystemstamp));
   return true;
}

inline bool get_boot_time_str(char *bootstamp_str, std::size_t &s) //will write BootstampLength chars
{
   if(s < (BootstampLength*2))
      return false;
   system_timeofday_information info;
   bool ret = get_system_time_of_day_information(info);
   if(!ret){
      return false;
   }
   const char Characters [] =
      { '0', '1', '2', '3', '4', '5', '6', '7'
      , '8', '9', 'A', 'B', 'C', 'D', 'E', 'F' };
   std::size_t char_counter = 0;
   for(std::size_t i = 0; i != static_cast<std::size_t>(BootstampLength); ++i){
      bootstamp_str[char_counter++] = Characters[(info.Reserved1[i]&0xF0)>>4];
      bootstamp_str[char_counter++] = Characters[(info.Reserved1[i]&0x0F)];
   }
   s = BootstampLength*2;
   return true;
}

inline bool get_boot_and_system_time_wstr(wchar_t *bootsystemstamp, std::size_t &s)  //will write BootAndSystemstampLength chars
{
   if(s < (BootAndSystemstampLength*2))
      return false;
   system_timeofday_information info;
   bool ret = get_system_time_of_day_information(info);
   if(!ret){
      return false;
   }
   const wchar_t Characters [] =
      { L'0', L'1', L'2', L'3', L'4', L'5', L'6', L'7'
      , L'8', L'9', L'A', L'B', L'C', L'D', L'E', L'F' };
   std::size_t char_counter = 0;
   for(std::size_t i = 0; i != static_cast<std::size_t>(BootAndSystemstampLength); ++i){
      bootsystemstamp[char_counter++] = Characters[(info.Reserved1[i]&0xF0)>>4];
      bootsystemstamp[char_counter++] = Characters[(info.Reserved1[i]&0x0F)];
   }
   s = BootAndSystemstampLength*2;
   return true;
}

class handle_closer
{
   void *handle_;
   handle_closer(const handle_closer &);
   handle_closer& operator=(const handle_closer &);
   public:
   explicit handle_closer(void *handle) : handle_(handle){}
   ~handle_closer()
   {  close_handle(handle_);  }
};

union ntquery_mem_t
{
   object_name_information_t name;
   struct ren_t
   {
      file_rename_information_t info;
      wchar_t buf[32767];
   } ren;
};

inline bool unlink_file(const char *filename)
{
   //Don't try to optimize doing a DeleteFile first
   //as there are interactions with permissions and
   //in-use files.
   //
   //if(!delete_file(filename)){
   //   (...)
   //

   //This functions tries to emulate UNIX unlink semantics in windows.
   //
   //- Open the file and mark the handle as delete-on-close
   //- Rename the file to an arbitrary name based on a random number
   //- Close the handle. If there are no file users, it will be deleted.
   //  Otherwise it will be used by already connected handles but the
   //  file name can't be used to open this file again
   try{
      NtSetInformationFile_t pNtSetInformationFile =
         (NtSetInformationFile_t)dll_func::get(dll_func::NtSetInformationFile);
      if(!pNtSetInformationFile){
         return false;
      }

      NtQueryObject_t pNtQueryObject =
         (NtQueryObject_t)dll_func::get(dll_func::NtQueryObject);

      //First step: Obtain a handle to the file using Win32 rules. This resolves relative paths
      void *fh = create_file(filename, generic_read | delete_access, open_existing,
         file_flag_backup_semantics | file_flag_delete_on_close, 0);
      if(fh == invalid_handle_value){
         return false;
      }

      handle_closer h_closer(fh);

      std::auto_ptr<ntquery_mem_t> pmem(new ntquery_mem_t);
      file_rename_information_t *pfri = &pmem->ren.info;
      const std::size_t RenMaxNumChars =
         ((char*)pmem.get() - (char*)&pmem->ren.info.FileName[0])/sizeof(wchar_t);

      //Obtain file name
      unsigned long size;
      if(pNtQueryObject(fh, object_name_information, pmem.get(), sizeof(ntquery_mem_t), &size)){
         return false;
      }

      //Copy filename to the rename member
      std::memmove(pmem->ren.info.FileName, pmem->name.Name.Buffer, pmem->name.Name.Length);
      std::size_t filename_string_length = pmem->name.Name.Length/sizeof(wchar_t);

      //Second step: obtain the complete native-nt filename
      //if(!get_file_name_from_handle_function(fh, pfri->FileName, RenMaxNumChars, filename_string_length)){
      //return 0;
      //}

      //Add trailing mark
      if((RenMaxNumChars-filename_string_length) < (SystemTimeOfDayInfoLength*2)){
         return false;
      }

      //Search '\\' character to replace it
      for(std::size_t i = filename_string_length; i != 0; --filename_string_length){
         if(pmem->ren.info.FileName[--i] == L'\\')
            break;
      }

      //Add random number
      std::size_t s = RenMaxNumChars - filename_string_length;
      if(!get_boot_and_system_time_wstr(&pfri->FileName[filename_string_length], s)){
         return false;
      }
      filename_string_length += s;

      //Fill rename information (FileNameLength is in bytes)
      pfri->FileNameLength = static_cast<unsigned long>(sizeof(wchar_t)*(filename_string_length));
      pfri->Replace = 1;
      pfri->RootDir = 0;

      //Final step: change the name of the in-use file:
      io_status_block_t io;
      if(0 != pNtSetInformationFile(fh, &io, pfri, sizeof(ntquery_mem_t::ren_t), file_rename_information)){
         return false;
      }
      return true;
   }
   catch(...){
      return false;
   }
   return true;
}

struct reg_closer
{
   //reg_closer(RegCloseKey_t func, void *key) : func_(func), key_(key){}
   //~reg_closer(){ (*func_)(key_);  }
   //RegCloseKey_t func_;
   void *key_;
   reg_closer(void *key) : key_(key){}
   ~reg_closer(){ reg_close_key(key_);  }
};

inline void get_shared_documents_folder(std::string &s)
{
   s.clear();
   void *key;
   if (reg_open_key_ex( hkey_local_machine
                     , "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders"
                     , 0
                     , key_query_value
                     , &key) == 0){
      reg_closer key_closer(key);

      //Obtain the value
      unsigned long size;
      unsigned long type;
      const char *const reg_value = "Common AppData";
      //long err = (*pRegQueryValue)( key, reg_value, 0, &type, 0, &size);
      long err = reg_query_value_ex( key, reg_value, 0, &type, 0, &size);
      if(!err){
         //Size includes terminating NULL
         s.resize(size);
         //err = (*pRegQueryValue)( key, reg_value, 0, &type, (unsigned char*)(&s[0]), &size);
         err = reg_query_value_ex( key, reg_value, 0, &type, (unsigned char*)(&s[0]), &size);
         if(!err)
            s.erase(s.end()-1);
         (void)err;
      }
   }
}

inline void get_registry_value(const char *folder, const char *value_key, std::vector<unsigned char> &s)
{
   s.clear();
   void *key;
   if (reg_open_key_ex( hkey_local_machine
                     , folder
                     , 0
                     , key_query_value
                     , &key) == 0){
      reg_closer key_closer(key);

      //Obtain the value
      unsigned long size;
      unsigned long type;
      const char *const reg_value = value_key;
      //long err = (*pRegQueryValue)( key, reg_value, 0, &type, 0, &size);
      long err = reg_query_value_ex( key, reg_value, 0, &type, 0, &size);
      if(!err){
         //Size includes terminating NULL
         s.resize(size);
         //err = (*pRegQueryValue)( key, reg_value, 0, &type, (unsigned char*)(&s[0]), &size);
         err = reg_query_value_ex( key, reg_value, 0, &type, (unsigned char*)(&s[0]), &size);
         if(!err)
            s.erase(s.end()-1);
         (void)err;
      }
   }
}

struct co_uninitializer
{
   co_uninitializer(bool b_uninitialize)
      : m_b_uninitialize(b_uninitialize)
   {}

   ~co_uninitializer()
   {
      if(m_b_uninitialize){
         CoUninitialize();
      }
   }

   private:
   const bool m_b_uninitialize;
};

template<class Object>
struct com_releaser
{
   Object *&object_;
   com_releaser(Object *&object) : object_(object) {}
   ~com_releaser()  {  object_->Release();    object_ = 0;  }
};

inline bool get_wmi_class_attribute( std::wstring& strValue, const wchar_t *wmi_class, const wchar_t *wmi_class_var)
{
   //See example http://msdn.microsoft.com/en-us/library/aa390423%28v=VS.85%29.aspx
   //
   //See BOOST_INTERPROCESS_WINDOWS_COINIT_MODEL definition if you need to change the
   //default value of this macro in your application
   long co_init_ret = CoInitializeEx(0, BOOST_INTERPROCESS_WINDOWS_COINIT_MODEL);
   if(co_init_ret != S_OK_BIPC && co_init_ret != S_FALSE_BIPC && co_init_ret != RPC_E_CHANGED_MODE_BIPC)
      return false;
   co_uninitializer co_initialize_end(co_init_ret != RPC_E_CHANGED_MODE_BIPC);
   (void)co_initialize_end;

   bool bRet = false;
   long sec_init_ret = CoInitializeSecurity
      ( 0   //pVoid
      ,-1   //cAuthSvc
      , 0   //asAuthSvc
      , 0   //pReserved1
      , RPC_C_AUTHN_LEVEL_PKT_BIPC //dwAuthnLevel
      , RPC_C_IMP_LEVEL_IMPERSONATE_BIPC //dwImpLevel
      , 0   //pAuthList
      , EOAC_NONE_BIPC //dwCapabilities
      , 0   //pReserved3
      );
   if( 0 == sec_init_ret || RPC_E_TOO_LATE_BIPC == sec_init_ret)
   {
      IWbemLocator_BIPC * pIWbemLocator = 0;
      const wchar_t * bstrNamespace = L"root\\cimv2";

      if( 0 != CoCreateInstance(
            CLSID_WbemAdministrativeLocator,
            0,
            CLSCTX_INPROC_SERVER_BIPC | CLSCTX_LOCAL_SERVER_BIPC,
            IID_IUnknown, (void **)&pIWbemLocator)){
         return false;
      }

      com_releaser<IWbemLocator_BIPC> IWbemLocator_releaser(pIWbemLocator);

      IWbemServices_BIPC *pWbemServices = 0;

      if( 0 != pIWbemLocator->ConnectServer(
            bstrNamespace,  // Namespace
            0,          // Userid
            0,           // PW
            0,           // Locale
            0,              // flags
            0,           // Authority
            0,           // Context
            &pWbemServices
            )
         ){
         return false;
      }

      if( S_OK_BIPC != CoSetProxyBlanket(
            pWbemServices,
            RPC_C_AUTHN_DEFAULT_BIPC,
            RPC_C_AUTHZ_DEFAULT_BIPC,
            0,
            RPC_C_AUTHN_LEVEL_PKT_BIPC,
            RPC_C_IMP_LEVEL_IMPERSONATE_BIPC,
            0,
            EOAC_NONE_BIPC
            )
         ){
         return false;
      }

      com_releaser<IWbemServices_BIPC> IWbemServices_releaser(pWbemServices);

      strValue.clear();
      strValue += L"Select ";
      strValue += wmi_class_var;
      strValue += L" from ";
      strValue += wmi_class;

      IEnumWbemClassObject_BIPC * pEnumObject  = 0;

      if ( 0 != pWbemServices->ExecQuery(
            L"WQL",
            strValue.c_str(),
            //WBEM_FLAG_RETURN_IMMEDIATELY_BIPC,
            WBEM_FLAG_RETURN_WHEN_COMPLETE_BIPC | WBEM_FLAG_FORWARD_ONLY_BIPC,
            0,
            &pEnumObject
            )
         ){
         return false;
      }

      com_releaser<IEnumWbemClassObject_BIPC> IEnumWbemClassObject_releaser(pEnumObject);

      //WBEM_FLAG_FORWARD_ONLY_BIPC incompatible with Reset
      //if ( 0 != pEnumObject->Reset() ){
         //return false;
      //}

      wchar_variant vwchar;
      unsigned long uCount = 1, uReturned;
      IWbemClassObject_BIPC * pClassObject = 0;
      while( 0 == pEnumObject->Next( WBEM_INFINITE_BIPC, uCount, &pClassObject, &uReturned ) )
      {
         com_releaser<IWbemClassObject_BIPC> IWbemClassObject_releaser(pClassObject);
         if ( 0 == pClassObject->Get( L"LastBootUpTime", 0, &vwchar, 0, 0 ) ){
            bRet = true;
            strValue = vwchar.value.pbstrVal;
            VariantClear(&vwchar );
            break;
         }
      }
   }
   return bRet;
}

inline bool get_last_bootup_time( std::wstring& strValue )
{
   bool ret = get_wmi_class_attribute(strValue, L"Win32_OperatingSystem", L"LastBootUpTime");
   std::size_t timezone = strValue.find(L'+');
   if(timezone != std::wstring::npos){
      strValue.erase(timezone);
   }
   timezone = strValue.find(L'-');
   if(timezone != std::wstring::npos){
      strValue.erase(timezone);
   }
   return ret;
}

inline bool get_last_bootup_time( std::string& str )
{
   std::wstring wstr;
   bool ret = get_last_bootup_time(wstr);
   str.resize(wstr.size());
   for(std::size_t i = 0, max = str.size(); i != max; ++i){
      str[i] = '0' + (wstr[i]-L'0');
   }
   return ret;
}

inline bool is_directory(const char *path)
{
	unsigned long attrib = GetFileAttributesA(path);

	return (attrib != invalid_file_attributes &&
	        (attrib & file_attribute_directory));
}

inline bool get_file_mapping_size(void *file_mapping_hnd, __int64 &size)
{
   NtQuerySection_t pNtQuerySection =
      (NtQuerySection_t)dll_func::get(dll_func::NtQuerySection);
   //Obtain file name
   interprocess_section_basic_information info;
   unsigned long ntstatus =
      pNtQuerySection(file_mapping_hnd, section_basic_information, &info, sizeof(info), 0);
   if(ntstatus){
      return false;
   }
   size = info.section_size;
   return true;
}

inline bool get_semaphore_info(void *handle, long &count, long &limit)
{
   winapi::interprocess_semaphore_basic_information info;
   winapi::NtQuerySemaphore_t pNtQuerySemaphore =
         (winapi::NtQuerySemaphore_t)dll_func::get(winapi::dll_func::NtQuerySemaphore);
   unsigned int ret_len;
   long status = pNtQuerySemaphore(handle, winapi::semaphore_basic_information, &info, sizeof(info), &ret_len);
   if(status){
      return false;
   }
   count = info.count;
   limit = info.limit;
   return true;
}


}  //namespace winapi
}  //namespace interprocess
}  //namespace boost

#include <boost/interprocess/detail/config_end.hpp>

#endif //#ifdef BOOST_INTERPROCESS_WIN32_PRIMITIVES_HPP
