/** Opaque from the first frame; fast loads never show the delayed indicator. */
export function DeviceLoader({label,error}: {label:string;error?:string}) {
  return <div className={`device-loader${error?' has-error':''}`}>
    <div className="device-loader-content" role={error?'alert':'status'}>
      <span>{error || label}</span>
      {!error && <div className="device-loading-progress" role="progressbar" aria-label={label}><span/></div>}
    </div>
  </div>;
}
