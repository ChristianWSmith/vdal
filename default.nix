{ pkgs ? import <nixpkgs> {}
, shell ? false
, version ? "0.0.4"
}:

with pkgs;
with pkgs.lib;

python3Packages.buildPythonApplication rec {

  name = "vdal";
  inherit version;

  format = "other";

  buildInputs = [
    libportal-gtk4
    librsvg
    python3Full
  ]
  ++ optionals shell (
    [ # Development shell dependencies
    ]
  );

  nativeBuildInputs = [
    wrapGAppsHook
    glib
    gobject-introspection
  ];

  propagatedBuildInputs = with python3Packages; [
    cairosvg
    pygobject3
  ];

  src = if shell then null else ./src;

  installPhase = ''
    mkdir -p $out/bin
    cp $src/main.py $out/bin/vdal
    cp $src/scrub_cache.py $out/bin/vdal-scrub-cache
    chmod +x $out/bin/vdal
    chmod +x $out/bin/vdal-scrub-cache
  '';

  postInstall = ''
    gappsWrapperArgs+=(
      "--prefix" "PYTHONPATH" : "${python3Packages.makePythonPath propagatedBuildInputs}"
      "--set" "PYTHONNOUSERSITE" "1"
    )
  '';

  meta = {
    description = "Very Dumb Application Launcher";
    license = licenses.mit;
  };
}
