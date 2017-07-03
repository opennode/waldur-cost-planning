Name: waldur-cost-planning
Summary: Waldur cost planning plugin
Group: Development/Libraries
Version: 0.4.2
Release: 1.el7
License: MIT
Url: http://waldur.com
Source0: %{name}-%{version}.tar.gz

Requires: waldur-core >= 0.142.0
Requires: waldur-openstack >= 0.30.2
Requires: waldur-digitalocean >= 0.8.2
Requires: waldur-aws >= 0.9.2

Obsoletes: nodeconductor-cost-planning

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot

BuildRequires: python-setuptools

%description
Waldur cost planning plugin allows to get a price estimate without actually creating the infrastructure.

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
* Mon Jul 3 2017 Jenkins <jenkins@opennodecloud.com> - 0.4.2-1.el7
- New upstream release

* Fri Jun 30 2017 Jenkins <jenkins@opennodecloud.com> - 0.4.1-1.el7
- New upstream release

* Wed May 31 2017 Jenkins <jenkins@opennodecloud.com> - 0.4.0-1.el7
- New upstream release

* Tue May 23 2017 Jenkins <jenkins@opennodecloud.com> - 0.3.1-1.el7
- New upstream release

* Tue May 23 2017 Jenkins <jenkins@opennodecloud.com> - 0.3.0-1.el7
- New upstream release

* Sat Sep 17 2016 Jenkins <jenkins@opennodecloud.com> - 0.2.0-1.el7
- New upstream release

* Tue May 3 2016 Victor Mireyev <victor@opennodecloud.com> - 0.1.0-1.el7
- Initial version of the package
