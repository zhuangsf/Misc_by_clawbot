package com.kidsalbum.ui

import android.app.DatePickerDialog
import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.kidsalbum.databinding.ActivityRegisterBinding
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

class RegisterActivity : AppCompatActivity() {

    private lateinit var binding: ActivityRegisterBinding
    private var selectedBirthday: Calendar? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRegisterBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupListeners()
    }

    private fun setupListeners() {
        // 生日选择
        binding.tvBirthday.setOnClickListener {
            showDatePicker()
        }

        // 注册按钮
        binding.btnRegister.setOnClickListener {
            val nickname = binding.etNickname.text.toString()
            val phone = binding.etPhone.text.toString()
            val password = binding.etPassword.text.toString()

            if (nickname.isEmpty() || phone.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "请填写完整信息", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            // 模拟注册成功
            startActivity(Intent(this, HomeActivity::class.java))
            finish()
        }

        // 登录链接
        binding.tvLoginLink.setOnClickListener {
            finish()
        }
    }

    private fun showDatePicker() {
        val calendar = Calendar.getInstance()
        // 默认选择3年前
        calendar.add(Calendar.YEAR, -3)

        DatePickerDialog(
            this,
            { _, year, month, day ->
                selectedBirthday = Calendar.getInstance().apply {
                    set(year, month, day)
                }
                val dateFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
                binding.tvBirthday.text = dateFormat.format(selectedBirthday!!.time)
                binding.tvBirthday.setTextColor(getColor(com.kidsalbum.R.color.text_dark))
            },
            calendar.get(Calendar.YEAR),
            calendar.get(Calendar.MONTH),
            calendar.get(Calendar.DAY_OF_MONTH)
        ).show()
    }
}
