CALL :CONVERT pi_state
CALL :CONVERT pi_timeseries
CALL :CONVERT rtcDataConfig
CALL :CONVERT rtcObjectiveConfig
CALL :CONVERT rtcRuntimeConfig
CALL :CONVERT rtcToolsConfig

pause
EXIT /B

:CONVERT
	SET file_to_convert=%~1
	datamodel-codegen --input %file_to_convert%\generated\%file_to_convert%.json --input-file-type jsonschema --output %file_to_convert% --field-constraints --use-subclass-enum --use-schema-description --base-class hydrolib.core.io.rtc.basemodel.RtcBaseModel  

	EXIT /B