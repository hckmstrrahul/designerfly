export const CAMERA_STORAGE_KEY = 'designerfly.camera-preset';
export const CAMERA_PRESETS = [
 {name:'Angled',position:[4.2,9.3,7.6],target:[.3,.5,0],zoom:.8},
 {name:'Paper',position:[.1,8.85,4],target:[1.25,.85,0],zoom:2.5},
 {name:'Overhead',position:[.3,10,.001],target:[.3,.5,0],zoom:.8},
] as const;
export function cameraPresetIndex(value:string|null):number {
 return value!==null && /^[0-2]$/.test(value) ? Number(value) : 0;
}
export function savedCameraPreset():number {
 try{return cameraPresetIndex(localStorage.getItem(CAMERA_STORAGE_KEY));}catch{return 0;}
}
