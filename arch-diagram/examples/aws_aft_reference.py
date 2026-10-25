"""Example: AWS Control Tower Account Factory for Terraform (AFT) architecture."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from archdiag import Canvas  # noqa: E402

c = Canvas(2590, 1250)

# ---- containers (outer -> inner)
c.box(265, 42, 2500, 1005, "outer")
c.icon("@terraform", 1205, 52, 46)
c.text(1262, 86, "AFT Deployment Module", 24, "start")
c.box(308, 148, 2457, 980, "solid", "AFT Management Account", tab="aws")

c.box(372, 222, 1032, 953, "dashed", tab="code")
src = c.box(415, 530, 592, 787, "grey", "Source")
cc  = c.icon("aws/devtools/codecommit", 461, 598, label="AWS\nCodeCommit")
cb  = c.icon("aws/devtools/codebuild", 679, 595, label="AWS\nCodeBuild")
c.icon("@terraform", 758, 560, 44)
ddb = c.icon("aws/database/dynamodb", 897, 595, label="Amazon\nDynamoDB")

c.box(1072, 222, 1412, 953, "solid", "Control Tower\nManagement Account", tab="aws", size=20)
prov = c.box(1153, 353, 1331, 920, "grey", "Account\nProvisioning")
c.icon("aws/management/service-catalog", 1200, 482, label="AWS Service\nCatalog")
c.icon("aws/management/control-tower", 1200, 748, label="AWS Control\nTower")

c.box(1478, 222, 2414, 953, "dashed", tab="code")
aft = c.box(1539, 353, 1717, 920, "grey", "AFT Account\nProvisioning\nFramework and\nCustomizations")
c.icon("aws/integration/step-functions", 1586, 593, label="AWS Step\nFunctions")

cust = c.box(1785, 300, 2392, 920, "grey", "Account Customizations")
oss  = c.box(1815, 374, 2350, 608, "dotted")
c.icon("aws/devtools/codebuild", 1911, 448, label="AWS\nCodeBuild")
c.icon("@terraform", 2180, 438, 84, label="Terraform\nOpen Source")
tfcb = c.box(1818, 676, 2056, 876, "dotted")
c.icon("aws/devtools/codebuild", 1904, 701, label="AWS\nCodeBuild")
tfc  = c.box(2112, 678, 2350, 878, "dotted")
c.icon("@terraform", 2190, 698, 84, label="Terraform Cloud\nor\nTerraform Enterprise", size=21)

vend = c.box(501, 1081, 2339, 1210, "solid", "Vended Account", tab="aws")
dev  = c.icon("onprem/client/users", 70, 588, 92, label="Developers")

# ---- arrows: attach to edges via ports, route explicitly
Y = cc.cy
c.arrow((dev.x2 - 2, Y), cc.left(Y))
c.arrow(cc.right(Y), cb.left(Y))
c.arrow(cb.right(Y), ddb.left(Y))
c.arrow(ddb.right(Y), prov.left(Y))            # into the group edge, not the icon
c.arrow(prov.right(Y), aft.left(Y))
c.elbow(aft.right(Y), oss.left(491), via_x=1766)
c.elbow(aft.right(Y), tfcb.left(775), via_x=1766)
c.arrow(tfcb.right(775), tfc.left(775), color="accent", dashed=True)
c.arrow(prov.bottom(), vend.top(prov.cx), color="ink")
c.elbow(cust.bottom(), vend.top(1722), via_y=1038, color="ink")

c.save(sys.argv[1] if len(sys.argv) > 1 else "aft")
print("ok")
