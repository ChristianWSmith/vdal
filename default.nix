{ pkgs ? import <nixpkgs> {}
, shell ? false
, version ? "0.0.1"
}:

with pkgs;
with pkgs.lib;

stdenv.mkDerivation rec {

  name = "vdal";
  inherit version;

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
    glib
    gobject-introspection
  ];

  propagatedBuildInputs = with python3Packages; [
    pygobject3
  ];

  src = if shell then null else ./src;

  installPhase = ''
    mkdir -p $out/bin
    cp $src/main.py $out/bin/vdal
    chmod +x $out/bin/vdal
  '';

  meta = {
    description = "Very Dumb Application Launcher";
    license = licenses.mit;
  };
}
