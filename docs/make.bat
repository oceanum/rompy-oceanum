@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=source
set BUILDDIR=build

if "%1" == "" goto help

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.https://sphinx-doc.org/
	exit /b 1
)

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

:clean
echo.Removing everything under '%BUILDDIR%'
rmdir /s /q %BUILDDIR% 2>nul
goto end

:install
echo.Installing documentation dependencies...
pip install -e ".[docs]"
goto end

:dev
%SPHINXBUILD% -b html %SOURCEDIR% %BUILDDIR%\html %SPHINXOPTS% %O%
echo.Build finished. The HTML pages are in %BUILDDIR%\html.
goto end

:strict
%SPHINXBUILD% -W -b html %SOURCEDIR% %BUILDDIR%\html %SPHINXOPTS% %O%
goto end

:linkcheck
%SPHINXBUILD% -b linkcheck %SOURCEDIR% %BUILDDIR%\linkcheck %SPHINXOPTS% %O%
goto end

:setup-dev
echo.Setting up development environment for documentation...
pip install -e ".[docs]"
pip install sphinx-autobuild
echo.Setup complete. Use 'sphinx-autobuild' for live reload development.
goto end

:end
popd
