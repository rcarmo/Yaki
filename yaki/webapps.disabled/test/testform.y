<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
<head>
<title>python cgi test</title>
</head>
<body>
<h3>Request Parameters</h3>
<form method="post" action="snoop.sn" name="multistuff1" enctype="multipart/form-data">
<p>
	Upload file to Snooper page. Max size = <%=self.WebApp.getConfigItem("maxPOSTsize")%> bytes. 
	Any attempt to upload a larger file will be aborted by the server.
	<p><input type="file" name="file">
	<input type="hidden" name="hiddenValue" value="this value is hidden">
    <input type="submit" name="Submit" value="Submit to Snoop page">
</form>
<hr>
<form name=zz method=POST action="snoop.sn?command&amp;extraarg=extra">
<p>
First Name:
<input type=text size=20 name=firstname>
<br>
Last Name:
<input type=text size=20 name=lastname>
  <input type=submit value="Submit POST" name="submit2">
  <br>
</form>
<form name=xx method=GET action="snoop.sn">
<p>
First Name:
<input type=text size=20 name=firstname>
<br>
Last Name:
<input type=text size=20 name=lastname>
  <input type=submit value="Submit GET" name="submit3">
  <br>
</form>
<form name="foobar2" action="snoop.sn?command&amp;extraarg=extra" method=POST>
<p>
  <textarea name="body" rows="10" cols="76"></TEXTAREA>
<input type=submit value="send text"  name="submit">
</form>
<form method="post" action="test.y" name="multistuff2" enctype="multipart/form-data">
  <p>Password: 
    <input type="password" name="password">
    <select name="select">
      <option>Male</option>
      <option>Female</option>
      <option>Neuter</option>
    </select>
    <select name="select2" size="2">
      <option>Male</option>
      <option>Female</option>
      <option>Neuter</option>
    </select>
  </p>
  <p> 
    <input type="checkbox" name="checkbox1" value="check1_checked">Checkbox1
    <input type="radio" name="radiobutton" value="radio1_checked">Radio1<br>
    <input type="checkbox" name="checkbox2" value="check2_checked">Checkbox2 
    <input type="radio" name="radiobutton" value="radio2_checked">Radio2<br>
	<p>Upload file to Ypage. Max size = <%=self.WebApp.getConfigItem("maxPOSTsize")%> bytes. 
	Any attempt to upload a larger file will be aborted by the server.
	<p>
    <input type="file" name="file">
    <input type="image" name="submit" src="img/snakelets-small.png">
    <input type="submit" name="Submit" value="Submit to Ypage">
  </p>
</form>
<hr>
</body>
</html>
