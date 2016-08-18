Name: nodeconductor-cost-planning
Summary: NodeConductor cost planning plugin
Group: Development/Libraries
Version: 0.1.0
Release: 1.el7
License: MIT
Url: http://nodeconductor.com
Source0: %{name}-%{version}.tar.gz

Requires: nodeconductor >= 0.96.0
Requires: python-lxml >= 3.2.0
Requires: python-xhtml2pdf >= 0.0.6

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot

BuildRequires: python-setuptools

%description
NodeConductor cost planning plugin allows to get a price estimate without actually creating the infrastructure.

%prep
%setup -q -n %{name}-%{version}

%build
python setup.py build

%install
rm -rf %{buildroot}
python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --record=INSTALLED_FILES

%clean
rm -rf %{buildroot}

%files -f INSTALLED_FILES
%defattr(-,root,root)

%changelog
* Tue May 3 2016 Victor Mireyev <victor@opennodecloud.com> - 0.1.0-1.el7
- Initial version of the package
