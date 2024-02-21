
  function prepareWebApp(){
  
    document.addEventListener('click', e => {
      if (!e.target.closest('.cSelectHeader')) {
          const details = document.querySelectorAll('.cSelect');
          details.forEach(element => element.removeAttribute('open'));
      }});

    // =================== draggable div ===============================
    var draggableDiv = document.getElementById('handleDiv1');
    var offsetX, offsetY, isDragging = false;

    draggableDiv.addEventListener('mousedown', function (event) {
      if  (event.target.id == 'handleDiv1'){
        isDragging = true;
        offsetX = event.clientX - draggableDiv.getBoundingClientRect().left;
        offsetY = event.clientY - draggableDiv.getBoundingClientRect().top;
        draggableDiv.style.cursor = 'move';
        }
    });
    

    document.addEventListener('mousemove', function (event) {
        if (!isDragging) return;

        var x = event.clientX - offsetX;
        var y = event.clientY - offsetY;

        draggableDiv.style.left = x + 'px';
        draggableDiv.style.top = y + 'px';
    });

    document.addEventListener('mouseup', () => {
      isDragging = false;
      storePosition(document.getElementById('handleDiv1'));
    })  

    var delayedRenderMix = createDelayManager();
    // console.log(typeof(delayedRenderMix))
    // numbers and options change handlers
    tableDiv = document.querySelector('.table-div');
    if (tableDiv){
      tableDiv.addEventListener('change', ()=>delayedRenderMix(renderMix, 2000));
      tableDiv.addEventListener('input', ()=>delayedRenderMix(renderMix, 2000))
      console.log('listeners set')
    }
    ctrlDiv = document.querySelector('.control-panel');
    if (ctrlDiv) {
      ctrlDiv.addEventListener('change', ()=>delayedRenderMix(renderMix, 2000));
      ctrlDiv.addEventListener('input', ()=>delayedRenderMix(renderMix, 2000)) ;
    }

    // table structure change handling 
    structChangeObserver = new MutationObserver(()=>delayedRenderMix(renderMix, 2000))
    const config = {childList: true, subtree: true};
//    structChangeObserver.observe(tableDiv, config);

    div1 = document.getElementById('td1');
    div2 = document.getElementById('handleDiv1');
    placeDiv(div1, div2);
    //================================================================
    
    screen_div = document.getElementById('rs1')
    screen_div.addEventListener('click', (event) => {
      let rows = Array.from(screen_div.querySelectorAll('tr'));
      let row_i = rows.indexOf(event.target.closest('tr'));
      row = event.target.closest('tr');
      // исключаем 1 и последнюю и предпоследнюю строки.
      if (row_i !== 0 && row_i !== rows.length - 2 && row_i !== rows.length - 1) {
          // Используем toggle для добавления и удаления класса checkedRow
          row.classList.toggle('checkedRow');
      }
    });
    // document.getElementById('sb1').textContent = 'Table used: {{tableName}}';
    
  }

//  closure-function realisation for renderTimer storage between onedit event handler calls
  var createDelayManager = function() {
    var timer = 0;
    return function(callback, ms) {
      clearTimeout(timer);
      timer = setTimeout(callback, ms);
    };
  }


  function renderMix() {
    console.log('rendering...')
    let mixScreen = document.querySelector('.renderScreen');
    let styleBlock = document.head.querySelector('style');

    if (mixScreen){        
        mix_composition = JSON.stringify(collectTableData());
        ajaxRequest = new XMLHttpRequest();
        ajaxRequest.open('POST', '/render', true);
        ajaxRequest.setRequestHeader("Content-Type", "application/json");
        ajaxRequest.send(mix_composition);
        ajaxRequest.onload = function() {
          if (ajaxRequest.readyState == 4 && ajaxRequest.status == 200) {
            let responseData = JSON.parse(ajaxRequest.responseText);
            var mixRenderHTML = responseData[0];
            var mixID = responseData[1];
            
            // REMOVED AS IT WILL ADD NEW STYLES TO THE PAGE EACH REFRESH OF RENDER DIV
            // const splitter = /<style[\S\s]*>([\s\S]+)<\/style>([\s\S]+)/g ;
            // let [, style, table] = splitter.exec(mixRenderHTML);
            // let renderedStyle = document.createElement('style');
            // renderedStyle.setAttribute('type', 'text/css');
            // renderedStyle.textContent = style;
            // style = `\n<style type="text/css">${style}\n</style>`
            // let pageTitle = document.querySelector('head > title');
            // pageTitle.insertAdjacentHTML('afterend', style);

            // // insertion of table itself
            // mixScreen.innerHTML = table;            
            mixScreen.innerHTML = mixRenderHTML;
            idPlace = document.getElementById('mixID');
            idPlace.innerText = mixID;
            // console.log(table_name + `  [mixture preset ID: ${mixID}] `);

          }
        }
      }    
    }


  function collectTableData() {
    var conc_table = document.querySelector(".main_form_table");
    var rows = {};
    var hide = [];

    let mix_volume = document.getElementById('v_mix').value;
    let dna_volume = document.getElementById('v_dna').value;
    let n_samples  = document.getElementById('n_samples').value;
    let multiplier = {'ul': 1, 'ml': 1000} [document.getElementById('cSelect2').querySelector('input[name="item"]:checked').title];
    dna_volume = dna_volume * multiplier;
    mix_volume = mix_volume * multiplier;


    rows['mixParameters'] = [mix_volume, dna_volume, n_samples]
    rows['reagentTable'] = {}

 
    for (var i = 1; i < conc_table.rows.length - 1; i++) {
      // создаем массив значений, соответствующих ячейкам со 2й по предпоследнюю (для каждой ячейки проверяем, что ее номер больше 2)
      // и в таком случае берем значение из дочернего элемента (input) - если оно имеется, иначе - пустую строку. Если номер не больше 2 - берем
      // значение прямо из ячейки таблицы
 
      let reagHide = conc_table.rows[i].cells[0].querySelector('.toggleBox').checked;
      let rowData = Array.from(conc_table.rows[i].cells).slice(1, -1);
      // если форвард или реверс:
      // let reagent_div_title = rowData[0].firstElementChild.id.slice(2);
      let reagent = rowData[0].querySelector(".uInput").value;
      if (!reagHide) {hide.push(reagent)}

      let [cstock, cwork] = rowData.slice(1, 3).map((cell) => {
        const inputElement = cell.querySelector(".uInput");
        return inputElement ? inputElement.value : "";
      }); 
      let units = rowData[1].innerText;
      // убедимся, что нет пустых ячеек (иначе сообщение и выход из функции) и засунем массив объединенный по '\t' (строка) в массив строк "rows"
      if (rowData.every((value) => value !== ""))
        rows['reagentTable'][reagent] = [cstock, cwork, units];
      else {
        alert("Empty cell found in " + conc_table.rows[i].cells[1].innerText + " line. Please enter the appropriate values before saving.");
        return;
      }
    }
    rows['hidelist'] = hide;
    return rows;
  }


  function tdLift(liftButton) {
    let row = liftButton.parentNode.parentNode; // получаем строку
    let table = row.parentNode;
    if (row.rowIndex > 1){
      let upperLine = table.rows[row.rowIndex - 2];
      table.insertBefore(row.cloneNode(true), upperLine);
      table.removeChild(row);
      renderMix();
    }
  }

  function tdErase(eraseButton) {    
    let row = eraseButton.parentNode.parentNode;
    let table = row.parentNode;
    table.removeChild(row);
    renderMix();
  }

  function setUnits(element) {
    units = document.querySelector("#addUU").value;
    document.querySelectorAll(".add_units_span").forEach((element) => {
      element.textContent = units;
    });
  }

  function addNameToMix() {
    reag_name = document
      .querySelector("#addName").value.trim(' ', '').replace('  ', ' ');
    reag_name = reag_name.startsWith("f:") || reag_name.startsWith("r:") ? reag_name.substring(2) : reag_name;
    // short_reag_name = ["f:", "r:"].includes(reag_name.slice(0, 2).toLowerCase())
    //   ? reag_name.slice(2)
    //   : reag_name;
    
    
    stock_uInput = document.querySelector("#addStockC").value;
    reag_stock = Number(stock_uInput !== "" ? stock_uInput : 0);
    
    work_uInput = document.querySelector("#addWorkC").value;
    reag_work = Number(work_uInput !== "" ? work_uInput : 0);
    
    units_uInput = document.querySelector("#addUU").value;
    reag_units = units_uInput !== "" ? units_uInput : "x";

    included_reagents = [];
    document
      .querySelectorAll(".names_div")
      .forEach((cell) => included_reagents.push(cell.innerText.toLowerCase()));

    if (reag_stock <= reag_work) {
      
      alert(`Work concentration C_work (${reag_work}) should be lower then stock concentration C_stock (${reag_stock})`, "Ok");
      return;
    }

    if (
      included_reagents.includes(reag_name.toLowerCase()) 
      //||
      // included_reagents.includes(short_reag_name.toLowerCase())
    ) {
      alert("Duplicated reagent names aren't allowed!");
      return;
    }

    var rowHTMLtr = `   
    <tr class="reagent_row">
        <td class="check_cell">
          <div class="ctoggleBut" title="Show / hide ${reag_name} in the mix.">
            <input type="checkbox" class="toggleBox" id="checkbox_${reag_name}" checked />
            <span class="toggleHandle"></span>
            <span class="toggleBG"></span>
            <label class="toggleLabel tl1">show</label>
            <label class="toggleLabel tl2">hide</label>
          </div>            
        </td>

        <td class="table_cell" id="name_cell_${reag_name}"> 
            <div class="names_div" id="d_${reag_name}">
              <input 
              type = 'text'
              size = 10
              required
              class="uInput editName"
              id = "rName_${reag_name}_uInput"
              value = "${reag_name}"
              onkeydown="event.keyCode===13 && this.blur();"
              />                
            </div>
        </td>

        <td class="table_cell" id="Cstock_${reag_name}_cell" title="Click to change">                        
            <input type="number" size="4" min=0 max=999 required class="editC uInput" id="Cstock_${reag_name}_uInput"
                onkeyup="if(this.value > 1000) this.value = 1000; if(this.value < 0) this.value = 0" value=${reag_stock}
                onkeydown="event.keyCode===13 && this.blur();"/>
            <div class="units-div">${reag_units}</div>
            
        </td>                    

        <td class="table_cell" id="Cwork_${reag_name}_cell" title="Click to change">                        
            <input type="number" size="4" min=0 max=999 required class="editC uInput" id="Cworck_${reag_name}_uInput"
                onkeyup="if(this.value > 1000) this.value = 1000; if(this.value < 0) this.value = 0" value=${reag_work}
                onkeydown="event.keyCode===13 && this.blur();"/>
            <div class="units-div">${reag_units}</div>
            
        </td>                     

        <td class="action_cell"> 
            <button type="button" onclick="tdErase(this)" class="round_but_del" title='Exclude ${reag_name} from mix'>&#10006;</button
            ><button type="button" onclick="tdLift(this)" class="round_but_moveup" title='Move ${reag_name} up in mix'>▲</button>
        </td>

    </tr>
    `;

    if (reag_name.length > 0) {
      let table_rows = document.getElementById("conc_table").rows;
      let ins_index = table_rows.length > 2 ? table_rows.length - 1 : 0;
      table_rows[ins_index].insertAdjacentHTML("beforebegin", rowHTMLtr);
    }
    renderMix();
  }

  function saveRecipeData() {
    
    var rows = collectTableData();
    var recipe = '';

    for (let i = 0; i < rows.length; i++) {
      recipe = recipe + [rows[i]['reagent'], rows[i]['cstock'], rows[i]['cwork'], , rows[i]['units']].join('\t') + '\n';
    }

    // var recipe = rows.join("\n");
    // Формирование содержимого файла в формате TSV
    let fileContent =
      "data:text/tab-separated-values;charset=utf-8," +
      encodeURIComponent("#reagents	Cstock	Cwork	Units\n" + recipe);
    let temporaryLink = document.createElement("a");
    temporaryLink.href = fileContent;
    temporaryLink.download = "reagents_table.tsv";
    document.body.appendChild(temporaryLink);
    temporaryLink.click();
    document.body.removeChild(temporaryLink);
  }

  function checkTableName(){
    cselect = document.getElementById("cSelect1");
    if (cselect){
      let selected = cselect.querySelector('input[name="file_item"]:checked');
      if (selected) {
        option = selected.getAttribute('title')
        console.log('Table reloading from "'+option+'"')
        if (option === 'Choose table') chooseTableDialog()
        else ajaxTableReload(option)       
      }
    }     
  }

  function chooseTableDialog(){
    var fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = ".tsv"; 
    // fileInput.multiple = False; 
    fileInput.style.display = 'none'; 
    fileInput.id = 'dynamicFileInput'; 
  
    fileInput.addEventListener('change', function () {
      let selectedFile = fileInput.files[0];
      if (selectedFile) {ajaxTableReload(selectedFile.name);}
      else {console.log('Файл не выбран');}
      document.body.removeChild(fileInput);
    });
    document.body.appendChild(fileInput); // Этот код добавляет инпут на страницу
    fileInput.click();
  }


  function ajaxTableReload(tableName) {
    ajaxRequest = new XMLHttpRequest();
    ajaxRequest.open('GET', `/reload?file=${encodeURIComponent(tableName)}`, true)
    ajaxRequest.send();
    ajaxRequest.onload = function() {
      if (ajaxRequest.readyState == 4 && ajaxRequest.status == 200) {
//        responseArray = JSON.parse(ajaxRequest.responseText);
//        let newHTML = responseArray[0];
//        let title = responseArray[1]['title'];
        let newHTML = ajaxRequest.responseText;
        div1 = document.getElementById('td1');
        div2 = document.getElementById('handleDiv1');
        placeDiv(div1, div2);
        // Здесь вы обрабатываете полученный HTML-код
        document.documentElement.innerHTML = newHTML;
//        document.title = title;
        // document.getElementById('sb1').textContent = 'Table used: ' + title;
        prepareWebApp();
        renderMix();
      }
    }
  }

 function storePosition(element) {
  reactange = element.getBoundingClientRect();
  sessionStorage.setItem('element_top', reactange.top);
  sessionStorage.setItem('element_left', reactange.left);

 }

 function placeDiv(div1, div2) {
  let top = sessionStorage.getItem('element_top');
  let left = sessionStorage.getItem('element_left');
  
  if ((top !== null) && (left !== null)) {
    console.log('Draggable div placed using stored position')
    div2.style.top = `${top}px`;
    div2.style.left = `${left}px`;
  } 
  else {
      // оставшееся место справа от таблицы реагентов больше чем 2/3 от ее ширины
    if  ((window.innerWidth - (div1.offsetLeft + div1.offsetWidth)) > (div1.offsetWidth * 5/6)) {
      console.log('Draggable div placed on the right ...')
      div2.style.top = `${div1.offsetTop}px`;
      div2.style.left = `${div1.offsetLeft + div1.offsetWidth + 10}px`;
    }
    else {
      console.log('Draggable div placed under ...')
      div2.style.top = `${div1.offsetTop + div1.offsetHeight + 20}px`;
      div2.style.left = `${div1.offsetLeft}px`;
    } // else 1
  } // else 2
  
 }


function divToUint8Array(divElem) {
  return html2canvas(divElem).then(canvas => {
    const dataUrl = canvas.toDataURL('image/png');
    const byteString = atob(dataUrl.split(',')[1]);
    const uint8Array = new Uint8Array(byteString.length);

    for (let i = 0; i < byteString.length; i++) {
      uint8Array[i] = byteString.charCodeAt(i);
    }

    return uint8Array;
  });
}

function altCopy() {
  containerDiv = document.querySelector('#rs1.renderScreen');
  var userSelectDefaultValue = containerDiv.style.userSelect;
  containerDiv.style.userSelect = 'auto';

  divToUint8Array(containerDiv).then(uint8Array => {
    const textData = containerDiv.innerText;
    const htmlData = containerDiv.outerHTML;

    const clipboardItem = new ClipboardItem({
      "text/plain": new Blob([textData], { type: "text/plain" }),
      "text/html": new Blob([htmlData], { type: "text/html" }),
      "image/png": new Blob([uint8Array], { type: "image/png" })
    });

    navigator.clipboard.write([clipboardItem]).then(() => {
      alert('Copied to clipboard');
    }).catch(err => {
      console.error('Unable to copy to clipboard', err);
    }).finally(() => {
      // Восстанавливаем изначальное состояние userSelect
      containerDiv.style.userSelect = userSelectDefaultValue;
    });
  });
}


prepareWebApp();
renderMix();

