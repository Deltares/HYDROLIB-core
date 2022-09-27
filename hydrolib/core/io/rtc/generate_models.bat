CALL :CONVERT pi_state
CALL :CONVERT pi_timeseries
CALL :CONVERT rtcDataConfig
CALL :CONVERT rtcObjectiveConfig
CALL :CONVERT rtcRuntimeConfig
CALL :CONVERT rtcToolsConfig

pause
EXIT /B

:CONVERT
	SET file=%~1
	SET folder=%rtc_file%\generated
	datamodel-codegen --input %folder%\%file%.json --input-file-type jsonschema --output %file% --field-constraints --use-subclass-enum --use-schema-description --base-class hydrolib.core.io.rtc.basemodel.RtcBaseModel

	EXIT /B