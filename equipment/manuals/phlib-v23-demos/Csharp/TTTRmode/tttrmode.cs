
/************************************************************************

  C# demo access to TimeHarp 300 Hardware via PHLIB v 2.3.
  The program performs a measurement based on hardcoded settings.
  The resulting data is stored in a binary output file.

  Michael Wahl, PicoQuant GmbH, April 2009

  Note: This is a console application

  Tested with the following compilers:

  - MS Visual C# 2005 (Win 32 bit)
  - Mono 1.2.5 and 2.0.1 (Win 32 bit and Linux 32 bit)

************************************************************************/


using System; 				//for Console
using System.Text; 			//for StringBuilder 
using System.IO;			//for File
using System.Runtime.InteropServices;	//for DllImport




class HistoMode 
{

	//the following constants are taken from hhlib.defin

	const string PHLib ="phlib";
	const string TargetLibVersion ="2.3"; //this is what this program was written for

	const int MAXDEVNUM = 8;
	const int PH_ERROR_DEVICE_OPEN_FAIL = -1;
	const int MODE_T2 = 2;
	const int MODE_T3 = 3;
	const int TTREADMAX = 131072;
	const int FLAG_FIFOFULL = 0x0003;


	[DllImport(PHLib)]
	extern static int PH_GetLibraryVersion(StringBuilder vers);

	[DllImport(PHLib)]
	extern static int PH_GetErrorString(StringBuilder errstring, int errcode);

	[DllImport(PHLib)]
	extern static int PH_OpenDevice(int devidx, StringBuilder serial); 

	[DllImport(PHLib)]
	extern static int PH_Initialize(int devidx, int mode);

	[DllImport(PHLib)]
	extern static int PH_GetHardwareVersion(int devidx, StringBuilder model, StringBuilder version); 

	[DllImport(PHLib)]
	extern static int PH_Calibrate(int devidx);

	[DllImport(PHLib)]
	extern static int PH_SetSyncDiv(int devidx, int div);

	[DllImport(PHLib)]
	extern static int PH_SetCFDLevel(int devidx, int channel, int value);

	[DllImport(PHLib)]
	extern static int PH_SetCFDZeroCross(int devidx, int channel, int value);

	[DllImport(PHLib)]
	extern static int PH_SetRange(int devidx, int binning);

	[DllImport(PHLib)]
	extern static int PH_SetOffset(int devidx, int offset);

	[DllImport(PHLib)]
	extern static int PH_GetResolution(int devidx); 

	[DllImport(PHLib)]
	extern static int PH_GetCountRate(int devidx, int channel);

	[DllImport(PHLib)]
	extern static int PH_StartMeas(int devidx, int tacq);

	[DllImport(PHLib)]
	extern static int PH_StopMeas(int devidx);

	[DllImport(PHLib)]
	extern static int PH_CTCStatus(int devidx);

	[DllImport(PHLib)]
	extern static int PH_TTReadData(int devidx, uint[] buffer, int count);

	[DllImport(PHLib)]
	extern static int PH_GetFlags(int devidx); 
	
	[DllImport(PHLib)]
	extern static int PH_CloseDevice(int devidx);



	static void Main() 
	{

		int i,j;
		int retcode;
		int[] dev= new int[MAXDEVNUM];
		int found = 0;
		
		StringBuilder LibVer = new StringBuilder (8);
		StringBuilder Serial = new StringBuilder (8);
		StringBuilder Errstr = new StringBuilder (40);
		StringBuilder Model  = new StringBuilder (16);
		StringBuilder Version = new StringBuilder (8);

		int Mode = MODE_T2; //set T2 or T3 here, observe suitable Syncdivider and Range!

		int Range = 0;			//you can change this
		int Offset = 0; 
		int Tacq = 10000;		//Measurement time in millisec, you can change this
		int SyncDivider = 1;		//you can change this 
		int CFDZeroCross0 = 10;		//you can change this
		int CFDLevel0 = 50;		//you can change this
		int CFDZeroCross1 = 10;		//you can change this
		int CFDLevel1 = 50;		//you can change this
		int Resolution; 
		int Countrate0;
		int Countrate1;
		int flags = 0;
		int ctcstatus;
		int nRecords = 0; 
		long Progress = 0;

		uint[] buffer = new uint[TTREADMAX];

		FileStream  fs = null;
    		BinaryWriter bw = null;

		Console.WriteLine ("PicoHarp 300     PHLib Demo Application     M. Wahl, PicoQuant GmbH, 2009");
		Console.WriteLine ("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~");


		retcode = PH_GetLibraryVersion(LibVer);
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_GetLibraryVersion error {0}. Aborted.",Errstr);
        		goto ex;
 		}
		Console.WriteLine("PHLib Version is " + LibVer);

		if(LibVer.ToString() != TargetLibVersion)
		{
			Console.WriteLine("This program requires PHLib v." + TargetLibVersion);
        		goto ex;
 		}

		try
		{
			fs = File.Create("tttrmode.out");
    			bw = new BinaryWriter(fs);
		}
		catch ( Exception )
       		{
			Console.WriteLine("Error creating file");
			goto ex;
		}

		Console.WriteLine("Searching for PicoHarp devices...");
		Console.WriteLine("Devidx     Status");


		for(i=0;i<MAXDEVNUM;i++)
 		{
			retcode = PH_OpenDevice(i, Serial);  
			if(retcode==0) //Grab any HydraHarp we can open
			{
				Console.WriteLine("  {0}        S/N {1}", i, Serial);
				dev[found]=i; //keep index to devices we want to use
				found++;
			}
			else
			{
				if(retcode==PH_ERROR_DEVICE_OPEN_FAIL)
					Console.WriteLine("  {0}        no device", i);
				else 
				{
					PH_GetErrorString(Errstr, retcode);
					Console.WriteLine("  {0}        S/N {1}", i, Errstr);
				}
			}
		}

		//In this demo we will use the first HydraHarp device we find, i.e. dev[0].
		//You can also use multiple devices in parallel.
		//You can also check for specific serial numbers, so that you always know 
		//which physical device you are talking to.

		if(found<1)
		{
			Console.WriteLine("No device available.");
			goto ex; 
 		}


		Console.WriteLine("Using device {0}",dev[0]);
		Console.WriteLine("Initializing the device...");

		retcode = PH_Initialize(dev[0],Mode); 
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_Initialize error {0}. Aborted.",Errstr);
        		goto ex;
 		}

		retcode = PH_GetHardwareVersion(dev[0],Model,Version); //this is only for information
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_GetHardwareInfo error {0}. Aborted.",Errstr);
			goto ex;
		}
		else
			Console.WriteLine("Found Model {0} Version {1}",Model,Version);

		Console.WriteLine("Calibrating...");
		retcode = PH_Calibrate(dev[0]);
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_Calibrate Error {0}. Aborted.",Errstr);
			goto ex;
		}

		retcode = PH_SetSyncDiv(dev[0],SyncDivider);
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_SetSyncDiv Error {0}. Aborted.",Errstr);
			goto ex;
		}

		retcode = PH_SetCFDLevel(dev[0],0,CFDLevel0);
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_SetCFDLevel Error {0}. Aborted.",Errstr);
			goto ex;
		}

		retcode = PH_SetCFDZeroCross(dev[0],0, CFDZeroCross0);
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_SetCFDZeroCross Error {0}. Aborted.",Errstr);
			goto ex;
		}

		retcode = PH_SetCFDLevel(dev[0],1,CFDLevel1);
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_SetCFDLevel Error {0}. Aborted.",Errstr);
			goto ex;
		}

		retcode = PH_SetCFDZeroCross(dev[0],1, CFDZeroCross1);
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_SetCFDZeroCross Error {0}. Aborted.",Errstr);
			goto ex;
		}

		retcode = PH_SetRange(dev[0],Range);
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_SetRange Error {0}. Aborted.",Errstr);
			goto ex;
		}

		retcode = PH_SetOffset(dev[0],Offset);
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_SetOffset Error {0}. Aborted.",Errstr);
			goto ex;
		}

		retcode = PH_GetResolution(dev[0]);
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_GetResolution Error {0}. Aborted.",Errstr);
			goto ex;
		}
		else Resolution = retcode;

		Console.WriteLine("Resolution is {0} ps", Resolution);

		//Note: after Init or SetSyncDiv you must allow >100 ms for valid new count rate readings
		System.Threading.Thread.Sleep( 200 );

		retcode = PH_GetCountRate(dev[0], 0);
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_GetCountRate Error {0}. Aborted.",Errstr);
			goto ex;
		}
		else Countrate0 = retcode;
		Console.WriteLine("Countrate0 = {0}/s", Countrate0);

		retcode = PH_GetCountRate(dev[0], 1);
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_GetCountRate Error {0}. Aborted.",Errstr);
			goto ex;
		}
		else Countrate1 = retcode;
		Console.WriteLine("Countrate1 = {0}/s", Countrate1);

		Console.WriteLine();


		retcode = PH_StartMeas(dev[0],Tacq); 
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_StartMeas Error {0}. Aborted.",Errstr);
			goto ex;
		}

		while(true)
		{ 
        		retcode = PH_GetFlags(dev[0]);
			if(retcode<0)
			{
				PH_GetErrorString(Errstr, retcode);
				Console.WriteLine("PH_GetFlags Error {0}. Aborted.",Errstr);
				goto ex;
			}
			else flags = retcode;
        
			if ((flags&FLAG_FIFOFULL) != 0) 
			{
				Console.WriteLine();
				Console.WriteLine("FiFo Overrun!"); 
				goto stoptttr;
			}
		
			retcode = PH_TTReadData(dev[0], buffer, TTREADMAX);	//may return less!  
			if(retcode<0)
			{
				PH_GetErrorString(Errstr, retcode);
				Console.WriteLine();
				Console.WriteLine("PH_GetFlags Error {0}. Aborted.",Errstr);
				goto ex;
			}
			else nRecords = retcode;

			if(nRecords>0) 
			{

				for(j= 0;j<nRecords; j++)  
					bw.Write(buffer[j]); 
				
				Progress += nRecords;
				Console.Write("\b\b\b\b\b\b\b\b\b{0,9}",Progress);
			}
			else
			{
		  		retcode = PH_CTCStatus(dev[0]);
				if(retcode<0)
				{
					PH_GetErrorString(Errstr, retcode);
					Console.WriteLine("PH_CTCStatus Error {0}. Aborted.",Errstr);
					goto ex;
				}
				else ctcstatus = retcode;
				if (ctcstatus>0) 
				{ 
					Console.WriteLine();
					Console.WriteLine("Done"); 
					goto stoptttr; 
				}  
			}

			//within this loop you can also read the count rates if needed.
		}
  
stoptttr:
		Console.WriteLine();

		retcode = PH_StopMeas(dev[0]); 
		if(retcode<0)
		{
			PH_GetErrorString(Errstr, retcode);
			Console.WriteLine("PH_StopMeas Error {0}. Aborted.",Errstr);
			goto ex;
		}

		bw.Close(); 
    		fs.Close(); 

ex:


		for(i=0;i<MAXDEVNUM;i++) //no harm to close all
		{
			PH_CloseDevice(i);
		}

		Console.WriteLine("press RETURN to exit");
		Console.ReadLine();

	}

}



