using System;
using System.IO;
using VGAudio.Containers.Wave;
using VGAudio.Containers.Hca;

if (args.Length < 2) { Console.Error.WriteLine("usage: hcaenc <in.wav> <out.hca>"); return 1; }
var audio = new WaveReader().Read(File.ReadAllBytes(args[0]));
var hca = new HcaWriter().GetFile(audio);
File.WriteAllBytes(args[1], hca);
Console.WriteLine($"OK -> {args[1]} ({new FileInfo(args[1]).Length} bytes)");
return 0;
