@echo off
echo ================================================
echo   SecureDroid - Gradle Wrapper Fix Script
echo ================================================
echo.

SET PROJECT_DIR=C:\Users\krish\Downloads\SecureDroid_Full_Project\SecureDroid\android_app

echo [1/5] Navigating to project folder...
cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    echo ERROR: Could not find project folder!
    echo Please edit this script and update PROJECT_DIR to your correct path.
    pause
    exit /b 1
)
echo     OK: %PROJECT_DIR%

echo.
echo [2/5] Creating gradle/wrapper folder...
if not exist "gradle\wrapper" mkdir gradle\wrapper
echo     OK: gradle\wrapper created

echo.
echo [3/5] Downloading gradle-wrapper.jar from GitHub...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/gradle/gradle/v8.6.0/gradle/wrapper/gradle-wrapper.jar' -OutFile 'gradle\wrapper\gradle-wrapper.jar'}"
if exist "gradle\wrapper\gradle-wrapper.jar" (
    echo     OK: gradle-wrapper.jar downloaded
) else (
    echo     FAILED: Could not download. Trying alternate source...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/gradle/gradle/raw/v8.6.0/gradle/wrapper/gradle-wrapper.jar' -OutFile 'gradle\wrapper\gradle-wrapper.jar'}"
)

echo.
echo [4/5] Creating gradle-wrapper.properties...
(
echo distributionBase=GRADLE_USER_HOME
echo distributionPath=wrapper/dists
echo distributionUrl=https\://services.gradle.org/distributions/gradle-8.6-bin.zip
echo networkTimeout=10000
echo validateDistributionUrl=true
echo zipStoreBase=GRADLE_USER_HOME
echo zipStorePath=wrapper/dists
) > gradle\wrapper\gradle-wrapper.properties
echo     OK: gradle-wrapper.properties created

echo.
echo [5/5] Creating gradlew.bat...
(
echo @rem
echo @rem Copyright 2015 the original author or authors.
echo @rem
echo @if "%%DEBUG%%"=="" @echo off
echo @rem ##########################################################################
echo @rem  Gradle startup script for Windows
echo @rem ##########################################################################
echo setlocal
echo set DIRNAME=%%~dp0
echo if "%%DIRNAME%%"=="" set DIRNAME=.
echo set APP_BASE_NAME=%%~n0
echo set APP_HOME=%%DIRNAME%%
echo set CLASSPATH=%%APP_HOME%%\gradle\wrapper\gradle-wrapper.jar
echo ^"%%JAVA_HOME%%\bin\java.exe^" -classpath ^"%%CLASSPATH%%^" org.gradle.wrapper.GradleWrapperMain %%*
echo endlocal
) > gradlew.bat
echo     OK: gradlew.bat created

echo.
echo ================================================
echo   Checking settings.gradle...
echo ================================================
if not exist "settings.gradle" (
    echo Creating settings.gradle...
    (
        echo pluginManagement {
        echo     repositories {
        echo         google^(^)
        echo         mavenCentral^(^)
        echo         gradlePluginPortal^(^)
        echo     }
        echo }
        echo dependencyResolutionManagement {
        echo     repositoriesMode.set^(RepositoriesMode.FAIL_ON_PROJECT_REPOS^)
        echo     repositories {
        echo         google^(^)
        echo         mavenCentral^(^)
        echo     }
        echo }
        echo rootProject.name = "SecureDroid"
        echo include ':app'
    ) > settings.gradle
    echo     OK: settings.gradle created
) else (
    echo     OK: settings.gradle already exists
)

if not exist "build.gradle" (
    echo Creating root build.gradle...
    (
        echo plugins {
        echo     id 'com.android.application' version '8.2.2' apply false
        echo }
    ) > build.gradle
    echo     OK: root build.gradle created
) else (
    echo     OK: root build.gradle already exists
)

echo.
echo ================================================
echo   ALL DONE!
echo ================================================
echo.
echo Now go to Android Studio and click:
echo   File ^> Sync Project with Gradle Files
echo.
echo If it still fails, open the Build tab and share
echo the new error message.
echo.
pause
